/**
 * DAGPanel.jsx
 * ─────────────────────────────────────────────────────────────────────────────
 * Visualises the Directed Acyclic Graph (DAG) produced by the backend.
 *
 * Key differences from ASTPanel:
 *  • Uses a flat node-list layout (no tree assumption — nodes can have multiple
 *    in-edges in a DAG)
 *  • Shared/CSE nodes rendered with a golden glow + "×N" label suffix
 *  • Variable-label annotations shown as small "tag" nodes below each expression
 *  • Uses the same fitView/isVisible trick as ASTPanel to avoid 0×0 canvas bug
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  Background,
  Controls,
  useReactFlow,
  useNodesState,
  useEdgesState,
  MarkerType,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Share2, AlertCircle, Info } from 'lucide-react';

// ─── Design tokens (mirrors ASTPanel types, plus DAG-specific) ───────────────
const DAG_TYPE_META = {
  BinaryExpression: { bg: '#071e2e', border: '#0891b2', glow: 'rgba(8,145,178,0.5)',   dot: '#22d3ee' },
  Identifier:       { bg: '#042014', border: '#16a34a', glow: 'rgba(22,163,74,0.4)',   dot: '#4ade80' },
  Literal:          { bg: '#1f1200', border: '#d97706', glow: 'rgba(217,119,6,0.4)',   dot: '#fbbf24' },
  AssignmentExpression: { bg: '#120b2e', border: '#9333ea', glow: 'rgba(147,51,234,0.45)', dot: '#d8b4fe' },
  ReturnStatement:  { bg: '#130015', border: '#9333ea', glow: 'rgba(147,51,234,0.4)', dot: '#d8b4fe' },
  __label:          { bg: '#0d2b1f', border: '#059669', glow: 'rgba(5,150,105,0.35)', dot: '#34d399' },
  __shared:         { bg: '#1f1400', border: '#d97706', glow: 'rgba(245,158,11,0.65)', dot: '#fbbf24' },
};
const DAG_DEFAULT_META = { bg: '#1e293b', border: '#475569', glow: 'rgba(71,85,105,0.3)', dot: '#94a3b8' };

function dagMeta(node) {
  if (node.shared) return DAG_TYPE_META.__shared;
  return DAG_TYPE_META[node.type] || DAG_DEFAULT_META;
}

// ─── Label builder ────────────────────────────────────────────────────────────
function dagNodeLabel(node) {
  const suffix = node.shared ? `  ×${node.labels.length}` : '';
  switch (node.type) {
    case 'BinaryExpression':     return `Binary Expr (${node.operator})${suffix}`;
    case 'AssignmentExpression': return `Assignment (=)${suffix}`;
    case 'Identifier':           return `Identifier (${node.name})${suffix}`;
    case 'Literal':              return `Literal (${node.value})${suffix}`;
    case 'ReturnStatement':      return `Return${suffix}`;
    default:                     return `${node.type}${suffix}`;
  }
}

function dagTooltip(node) {
  const lines = [`Type     : ${node.type}`];
  if (node.operator) lines.push(`Operator : ${node.operator}`);
  if (node.name)     lines.push(`Name     : ${node.name}`);
  if (node.value)    lines.push(`Value    : ${node.value}`);
  if (node.labels?.length) lines.push(`Assigns  : ${node.labels.join(', ')}`);
  if (node.shared)   lines.push(`★ Common subexpression`);
  return lines.join('\n');
}

// ─── Custom DAG node renderer ─────────────────────────────────────────────────
function DAGNodeComponent({ data, selected }) {
  const isSelected = selected || data.highlighted;
  const isLabel    = data.isLabelNode;

  if (isLabel) {
    return (
      <div className="dag-node dag-node-label-tag" title={data.tooltip}>
        <span className="dag-node-label">{data.label}</span>
        <div className="ast-node-tooltip">{data.tooltip}</div>
      </div>
    );
  }

  return (
    <div
      className={[
        'ast-node dag-node',
        data.shared   ? 'dag-node-shared'   : '',
        isSelected    ? 'ast-node-selected' : '',
      ].join(' ')}
      style={{ '--nb': data.border, '--nbg': data.bg, '--nglow': data.glow }}
    >
      <span className="ast-node-dot" style={{ background: data.dot }} />
      <span className="ast-node-label">{data.label}</span>
      <div className="ast-node-tooltip">{data.tooltip}</div>
    </div>
  );
}

const DAG_NODE_TYPES = { dagNode: DAGNodeComponent };

// ─── Layout ───────────────────────────────────────────────────────────────────
const D_NODE_W  = 180;
const D_NODE_H  = 46;
const D_H_GAP   = 40;
const D_V_GAP   = 90;
const D_LABEL_H = 32;  // height of variable-label annotation nodes

/**
 * Topological sort + level assignment for a DAG.
 * Returns nodeId → depth.
 */
function assignDepths(nodes, edges) {
  const inDegree  = {};
  const children  = {};
  nodes.forEach(n => { inDegree[n.id] = 0; children[n.id] = []; });
  edges.forEach(e => {
    inDegree[e.target] = (inDegree[e.target] || 0) + 1;
    if (!children[e.source]) children[e.source] = [];
    children[e.source].push(e.target);
  });

  const depths = {};
  const queue  = nodes.filter(n => inDegree[n.id] === 0).map(n => n.id);
  queue.forEach(id => { depths[id] = 0; });

  while (queue.length) {
    const cur = queue.shift();
    for (const child of (children[cur] || [])) {
      depths[child] = Math.max(depths[child] || 0, depths[cur] + 1);
      inDegree[child]--;
      if (inDegree[child] === 0) queue.push(child);
    }
  }
  return depths;
}

function layoutDAG(dagNodes, dagEdges) {
  if (!dagNodes.length) return { rfNodes: [], rfEdges: [] };

  const depths      = assignDepths(dagNodes, dagEdges);
  const maxDepth    = Math.max(...Object.values(depths), 0);
  const byDepth     = Array.from({ length: maxDepth + 1 }, () => []);
  dagNodes.forEach(n => byDepth[depths[n.id] ?? 0].push(n));

  const rfNodes = [];
  const rfEdges = [];
  const posMap  = {};  // nodeId → {x, y}

  // Position expression nodes on a grid
  byDepth.forEach((level, depth) => {
    const totalW = level.length * D_NODE_W + (level.length - 1) * D_H_GAP;
    const startX = -totalW / 2;
    level.forEach((n, i) => {
      const meta = dagMeta(n);
      const x    = startX + i * (D_NODE_W + D_H_GAP);
      const y    = depth * (D_NODE_H + D_V_GAP);
      posMap[n.id] = { x, y };

      rfNodes.push({
        id:       n.id,
        type:     'dagNode',
        position: { x, y },
        data: {
          ...meta,
          label:       dagNodeLabel(n),
          tooltip:     dagTooltip(n),
          shared:      !!n.shared,
          highlighted: false,
          isLabelNode: false,
        },
      });

      // Render variable-label annotation nodes below the expression node
      if (n.labels && n.labels.length) {
        n.labels.forEach((lbl, li) => {
          const lblId = `lbl-${n.id}-${li}`;
          const lblX  = x + li * (D_NODE_W / Math.max(n.labels.length, 1)) - (n.labels.length > 1 ? D_NODE_W / 4 : 0);
          const lblY  = y + D_NODE_H + D_V_GAP * 0.45;
          rfNodes.push({
            id:       lblId,
            type:     'dagNode',
            position: { x: lblX, y: lblY },
            data: {
              ...DAG_TYPE_META.__label,
              label:       `→ ${lbl}`,
              tooltip:     `Variable "${lbl}" is assigned this expression`,
              shared:      false,
              highlighted: false,
              isLabelNode: true,
            },
          });
          rfEdges.push({
            id:       `e-lbl-${n.id}-${li}`,
            source:   n.id,
            target:   lblId,
            type:     'smoothstep',
            style:    { stroke: '#059669', strokeWidth: 1.2, strokeDasharray: '5 4', opacity: 0.7 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#059669', width: 10, height: 10 },
          });
        });
      }
    });
  });

  // Add edges for actual DAG graph edges
  dagEdges.forEach((e, i) => {
    const meta = dagMeta(dagNodes.find(n => n.id === e.target) || {});
    rfEdges.push({
      id:       `dag-e-${i}-${e.source}-${e.target}`,
      source:   e.source,
      target:   e.target,
      type:     'smoothstep',
      animated: false,
      markerEnd: { type: MarkerType.ArrowClosed, color: meta.border, width: 12, height: 12 },
      style:    { stroke: meta.border, strokeWidth: 1.6, opacity: 0.8 },
    });
  });

  return { rfNodes, rfEdges };
}

// ─── Inner ReactFlow canvas ───────────────────────────────────────────────────
function DAGFlowInner({ dagJson, isVisible }) {
  const { fitView } = useReactFlow();

  const { rfNodes: initNodes, rfEdges: initEdges } = useMemo(() => {
    if (!dagJson) return { rfNodes: [], rfEdges: [] };
    return layoutDAG(dagJson.nodes || [], dagJson.edges || []);
  }, [dagJson]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initNodes);
  const [edges, , onEdgesChange]         = useEdgesState(initEdges);
  const [selectedId, setSelectedId]      = useState(null);

  useEffect(() => {
    if (isVisible) {
      const t = setTimeout(() => fitView({ padding: 0.28, duration: 350 }), 80);
      return () => clearTimeout(t);
    }
  }, [isVisible, fitView]);

  const handleNodeClick = useCallback((_, node) => {
    setSelectedId(prev => prev === node.id ? null : node.id);
  }, []);

  const displayNodes = useMemo(
    () => nodes.map(n => ({ ...n, data: { ...n.data, highlighted: n.id === selectedId } })),
    [nodes, selectedId]
  );

  return (
    <ReactFlow
      nodes={displayNodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={DAG_NODE_TYPES}
      onNodeClick={handleNodeClick}
      fitView
      fitViewOptions={{ padding: 0.28 }}
      minZoom={0.08}
      maxZoom={3}
      proOptions={{ hideAttribution: true }}
      nodesDraggable
      nodesConnectable={false}
      elevateEdgesOnSelect
    >
      <Background variant={BackgroundVariant.Dots} color="#1a2a1a" gap={26} size={1.4} />
      <Controls
        showInteractive={false}
        style={{
          background: 'rgba(10,18,36,0.9)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '10px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
        }}
      />
    </ReactFlow>
  );
}

function DAGFlow({ dagJson, isVisible }) {
  return (
    <ReactFlowProvider>
      <DAGFlowInner dagJson={dagJson} isVisible={isVisible} />
    </ReactFlowProvider>
  );
}

// ─── Legend ───────────────────────────────────────────────────────────────────
const DAG_LEGEND = [
  { label: 'Expression',   dot: DAG_TYPE_META.BinaryExpression.dot   },
  { label: 'Identifier',   dot: DAG_TYPE_META.Identifier.dot         },
  { label: 'Literal',      dot: DAG_TYPE_META.Literal.dot            },
  { label: 'Shared (CSE)', dot: DAG_TYPE_META.__shared.dot           },
  { label: 'Assigned to',  dot: DAG_TYPE_META.__label.dot            },
];

// ─── Public component ─────────────────────────────────────────────────────────
export function DAGPanel({ dagJson, hasSyntaxErrors, isVisible = true }) {

  if (hasSyntaxErrors) {
    return (
      <div className="empty-state">
        <AlertCircle style={{ width: 44, height: 44, color: '#f59e0b', marginBottom: '1rem' }} />
        <p style={{ color: '#f59e0b', fontWeight: 700, fontSize: '0.95rem', margin: 0 }}>
          DAG cannot be generated due to syntax errors
        </p>
        <p className="empty-state-subtext">
          Resolve lexical/syntax errors and re-analyze.
        </p>
      </div>
    );
  }

  if (!dagJson) {
    return (
      <div className="empty-state">
        <Share2 style={{ width: 44, height: 44, opacity: 0.22, marginBottom: '1rem' }} />
        <p>No DAG Available</p>
        <p className="empty-state-subtext">
          Click "Analyze Code" to generate the optimization DAG.
        </p>
      </div>
    );
  }

  const hasCse = dagJson.has_cse;

  return (
    <div className="ast-panel-root">
      {/* CSE / no-CSE info banner */}
      {hasCse ? (
        <div className="dag-cse-banner dag-cse-found">
          <Share2 style={{ width: 14, height: 14, flexShrink: 0 }} />
          <span>
            <strong>Common Subexpression Elimination applied</strong> — shared nodes (gold glow) appear once
            and are reused by multiple assignments.
          </span>
        </div>
      ) : (
        <div className="dag-cse-banner dag-cse-none">
          <Info style={{ width: 14, height: 14, flexShrink: 0 }} />
          <span>
            DAG is <strong>identical to AST</strong> — no common subexpressions found in this code.
          </span>
        </div>
      )}

      {/* Canvas */}
      <div className="ast-canvas" style={{ background: '#020f06' }}>
        <DAGFlow dagJson={dagJson} isVisible={isVisible} />
      </div>

      {/* Legend */}
      <div className="ast-legend">
        {DAG_LEGEND.map(item => (
          <span key={item.label} className="ast-legend-item">
            <span className="ast-legend-dot" style={{ background: item.dot }} />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}
