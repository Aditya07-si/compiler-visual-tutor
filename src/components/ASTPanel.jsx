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
import { GitBranch, AlertTriangle, AlertCircle } from 'lucide-react';

// ─── Design tokens ────────────────────────────────────────────────────────────
const TYPE_META = {
  Program:              { bg: '#1e1b4b', border: '#7c3aed', glow: 'rgba(124,58,237,0.5)',  dot: '#a78bfa', legendLabel: 'Program'             },
  Block:                { bg: '#0f1f3a', border: '#3b82f6', glow: 'rgba(59,130,246,0.35)', dot: '#93c5fd', legendLabel: 'Block'               },
  VarDeclaration:       { bg: '#071a36', border: '#1d4ed8', glow: 'rgba(29,78,216,0.35)',  dot: '#60a5fa', legendLabel: 'Declaration'          },
  AssignmentExpression: { bg: '#120b2e', border: '#9333ea', glow: 'rgba(147,51,234,0.4)',  dot: '#d8b4fe', legendLabel: 'Assignment'           },
  BinaryExpression:     { bg: '#071e2e', border: '#0891b2', glow: 'rgba(8,145,178,0.4)',   dot: '#22d3ee', legendLabel: 'Binary Expression'    },
  Identifier:           { bg: '#042014', border: '#16a34a', glow: 'rgba(22,163,74,0.35)',  dot: '#4ade80', legendLabel: 'Identifier'           },
  Literal:              { bg: '#1f1200', border: '#d97706', glow: 'rgba(217,119,6,0.35)',  dot: '#fbbf24', legendLabel: 'Literal'              },
  ReturnStatement:      { bg: '#130015', border: '#9333ea', glow: 'rgba(147,51,234,0.35)', dot: '#d8b4fe', legendLabel: 'Return'               },
  CallExpression:       { bg: '#081a22', border: '#0e7490', glow: 'rgba(14,116,144,0.35)', dot: '#67e8f9', legendLabel: 'Function Call'        },
};
const DEFAULT_META = { bg: '#1e293b', border: '#475569', glow: 'rgba(71,85,105,0.3)', dot: '#94a3b8', legendLabel: 'Node' };

// LEGEND_ITEMS only includes what's likely to appear
const LEGEND_ITEMS = [
  ['Program', TYPE_META.Program],
  ['VarDeclaration', TYPE_META.VarDeclaration],
  ['AssignmentExpression', TYPE_META.AssignmentExpression],
  ['BinaryExpression', TYPE_META.BinaryExpression],
  ['Identifier', TYPE_META.Identifier],
  ['Literal', TYPE_META.Literal],
  ['ReturnStatement', TYPE_META.ReturnStatement],
];

// ─── Label builder ────────────────────────────────────────────────────────────
function makeLabel(node) {
  switch (node.type) {
    case 'Program':              return 'Program';
    case 'Block':                return 'Block  { }';
    case 'VarDeclaration':       return `VarDecl (${node.varType} ${node.name})`;
    case 'AssignmentExpression': return 'Assignment (=)';
    case 'BinaryExpression':     return `Binary Expression (${node.operator})`;
    case 'Identifier':           return `Identifier (${node.name})`;
    case 'Literal':              return `Literal (${node.value})`;
    case 'ReturnStatement':      return 'Return Statement';
    case 'CallExpression':       return `Call  ${node.callee}(…)`;
    default:                     return node.type;
  }
}

// ─── Tooltip builder ──────────────────────────────────────────────────────────
function makeTooltip(node) {
  const lines = [`Type     : ${node.type}`];
  if (node.varType)  lines.push(`Var type : ${node.varType}`);
  if (node.name)     lines.push(`Name     : ${node.name}`);
  if (node.operator) lines.push(`Operator : ${node.operator}`);
  if (node.value)    lines.push(`Value    : ${node.value}`);
  if (node.dataType) lines.push(`Data type: ${node.dataType}`);
  if (node.callee)   lines.push(`Callee   : ${node.callee}`);
  if (node.line)     lines.push(`Src line : ${node.line}`);
  return lines.join('\n');
}

// ─── Node renderer ────────────────────────────────────────────────────────────
function ASTNodeComponent({ data, selected }) {
  const meta       = TYPE_META[data.nodeType] || DEFAULT_META;
  const isSelected = selected || data.highlighted;
  const isRoot     = data.isRoot;

  return (
    <div
      className={[
        'ast-node',
        isRoot     ? 'ast-node-root'     : '',
        isSelected ? 'ast-node-selected' : '',
      ].join(' ')}
      style={{ '--nb': meta.border, '--nbg': meta.bg, '--nglow': meta.glow }}
    >
      <span className="ast-node-dot" style={{ background: meta.dot }} />
      <span className="ast-node-label">{data.label}</span>
      <div className="ast-node-tooltip">{data.tooltip}</div>
    </div>
  );
}

const NODE_TYPES = { astNode: ASTNodeComponent };

// ─── Layout constants ─────────────────────────────────────────────────────────
// NODE_UNIT = the horizontal "slot" given to each leaf in the subtree grid.
// Reduce to tighten spacing; 150 keeps the tree compact without overlapping.
const NODE_UNIT = 150;   // px per leaf slot
const NODE_H    = 46;    // estimated rendered node height (px)
const V_GAP     = 85;    // vertical gap between depth levels (px)
const NODE_W    = 160;   // nominal node width (used to centre node in its slot)

// ─── Tree build + layout (two-phase) ─────────────────────────────────────────
let _uid = 0;
function uid() { return `n${_uid++}`; }

/** Recursively count leaf nodes — this is the "weight" of the subtree. */
function leafCount(jsonNode) {
  if (!jsonNode) return 0;
  const children = getChildren(jsonNode);
  if (children.length === 0) return 1;
  return children.reduce((s, c) => s + leafCount(c), 0);
}

/** Canonical child order matching the AST schema */
function getChildren(jsonNode) {
  const c = [];
  if (jsonNode.body)     jsonNode.body.forEach(n => n && c.push(n));
  if (jsonNode.init)     c.push(jsonNode.init);
  if (jsonNode.left)     c.push(jsonNode.left);
  if (jsonNode.right)    c.push(jsonNode.right);
  if (jsonNode.argument) c.push(jsonNode.argument);
  return c;
}

/**
 * Build React Flow nodes + edges and assign positions in one pass.
 * @param {object} jsonNode – AST JSON node
 * @param {string|null} parentId – React Flow node id of parent
 * @param {number} slotStart – leftmost x of this subtree's allocated band
 * @param {number} depth – depth level (root = 0)
 * @param {object[]} rfNodes – accumulated React Flow nodes
 * @param {object[]} rfEdges – accumulated React Flow edges
 * @param {boolean} isRoot – mark root node for emphasis
 */
function buildAndLayout(jsonNode, parentId, slotStart, depth, rfNodes, rfEdges, isRoot = false) {
  if (!jsonNode) return;

  const id       = uid();
  const leaves   = Math.max(leafCount(jsonNode), 1);
  const slotW    = leaves * NODE_UNIT;
  const cx       = slotStart + slotW / 2 - NODE_W / 2;   // centre node horizontally
  const cy       = depth * (NODE_H + V_GAP);

  const meta = TYPE_META[jsonNode.type] || DEFAULT_META;

  rfNodes.push({
    id,
    type: 'astNode',
    position: { x: cx, y: cy },
    data: {
      nodeType:    jsonNode.type,
      label:       makeLabel(jsonNode),
      tooltip:     makeTooltip(jsonNode),
      raw:         jsonNode,
      isRoot,
      highlighted: false,
    },
  });

  if (parentId) {
    rfEdges.push({
      id:     `e-${parentId}-${id}`,
      source: parentId,
      target: id,
      type:   'smoothstep',
      animated: false,
      markerEnd: {
        type:   MarkerType.ArrowClosed,
        color:  meta.border,
        width:  12,
        height: 12,
      },
      style: { stroke: meta.border, strokeWidth: 1.6, opacity: 0.75 },
    });
  }

  // Recurse over children
  let cursor = slotStart;
  for (const child of getChildren(jsonNode)) {
    const childLeaves = Math.max(leafCount(child), 1);
    buildAndLayout(child, id, cursor, depth + 1, rfNodes, rfEdges, false);
    cursor += childLeaves * NODE_UNIT;
  }
}

// ─── Inner ReactFlow canvas ───────────────────────────────────────────────────
function ASTFlowInner({ astJson, isVisible }) {
  const { fitView } = useReactFlow();

  const { initNodes, initEdges } = useMemo(() => {
    _uid = 0;
    const rfNodes = [], rfEdges = [];
    buildAndLayout(astJson, null, 0, 0, rfNodes, rfEdges, true);
    return { initNodes: rfNodes, initEdges: rfEdges };
  }, [astJson]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initNodes);
  const [edges, , onEdgesChange]         = useEdgesState(initEdges);
  const [selectedId, setSelectedId]      = useState(null);

  // Re-run fitView every time the panel becomes visible
  useEffect(() => {
    if (isVisible) {
      // Small delay lets the browser finish the CSS transition
      const t = setTimeout(() => fitView({ padding: 0.28, duration: 350 }), 80);
      return () => clearTimeout(t);
    }
  }, [isVisible, fitView]);

  const handleNodeClick = useCallback((_, node) => {
    setSelectedId(prev => (prev === node.id ? null : node.id));
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
      nodeTypes={NODE_TYPES}
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
      <Background
        variant={BackgroundVariant.Dots}
        color="#1e2d45"
        gap={26}
        size={1.4}
      />
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

function ASTFlow({ astJson, isVisible }) {
  return (
    <ReactFlowProvider>
      <ASTFlowInner astJson={astJson} isVisible={isVisible} />
    </ReactFlowProvider>
  );
}

// ─── Public component ─────────────────────────────────────────────────────────
export function ASTPanel({ astJson, astError, hasSyntaxErrors, hasSemanticErrors, isVisible = true }) {
  // ── Error: syntax blocks AST ────────────────────────────────────────────────
  if (hasSyntaxErrors || astError) {
    return (
      <div className="empty-state">
        <AlertTriangle style={{ width: 44, height: 44, color: '#f59e0b', marginBottom: '1rem' }} />
        <p style={{ color: '#f59e0b', fontWeight: 700, fontSize: '0.95rem', margin: 0 }}>
          AST cannot be generated due to syntax errors
        </p>
        <p className="empty-state-subtext">
          {astError || 'Resolve lexical and syntax errors, then re-analyze.'}
        </p>
      </div>
    );
  }

  // ── Empty: not yet analyzed ─────────────────────────────────────────────────
  if (!astJson) {
    return (
      <div className="empty-state">
        <GitBranch style={{ width: 44, height: 44, opacity: 0.22, marginBottom: '1rem' }} />
        <p>No AST Available</p>
        <p className="empty-state-subtext">
          Click "Analyze Code" to generate and view the Abstract Syntax Tree.
        </p>
      </div>
    );
  }

  // ── Full view ───────────────────────────────────────────────────────────────
  return (
    <div className="ast-panel-root">
      {/* Semantic warning */}
      {hasSemanticErrors && (
        <div className="ast-semantic-banner">
          <AlertCircle style={{ width: 14, height: 14, flexShrink: 0 }} />
          <span>
            <strong>AST generated with semantic warnings</strong> — tree is structurally valid but
            references undeclared variables or has type issues.
          </span>
        </div>
      )}

      {/* Canvas */}
      <div className="ast-canvas">
        <ASTFlow astJson={astJson} isVisible={isVisible} />
      </div>

      {/* Legend */}
      <div className="ast-legend">
        {LEGEND_ITEMS.map(([type, meta]) => (
          <span key={type} className="ast-legend-item">
            <span className="ast-legend-dot" style={{ background: meta.dot }} />
            {meta.legendLabel}
          </span>
        ))}
      </div>
    </div>
  );
}
