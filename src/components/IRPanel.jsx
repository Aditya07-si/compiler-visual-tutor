import React, { useState } from 'react';
import { Cpu, TerminalSquare, GitBranch, Code2, Share2 } from 'lucide-react';
import { ASTPanel } from './ASTPanel.jsx';
import { DAGPanel } from './DAGPanel.jsx';

export function IRPanel({
  irCode = [],
  astJson = null,
  astError = null,
  dagJson = null,
  hasSyntaxErrors = false,
  hasSemanticErrors = false,
}) {
  const [activeView, setActiveView] = useState('tac');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>

      {/* ── Header + 3-way toggle ────────────────────────────────────────── */}
      <div className="ir-panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Code2 style={{ width: 16, height: 16, color: 'var(--accent-color)' }} />
          <span className="ir-panel-title">Intermediate Representation</span>
        </div>

        <div className="ir-toggle-group">
          <button
            id="btn-show-tac"
            className={`ir-toggle-btn ${activeView === 'tac' ? 'ir-toggle-active' : ''}`}
            onClick={() => setActiveView('tac')}
            title="Show Three-Address Code"
          >
            <Cpu style={{ width: 13, height: 13 }} />
            TAC
          </button>
          <button
            id="btn-show-ast"
            className={`ir-toggle-btn ${activeView === 'ast' ? 'ir-toggle-active' : ''}`}
            onClick={() => setActiveView('ast')}
            title="Show Abstract Syntax Tree"
          >
            <GitBranch style={{ width: 13, height: 13 }} />
            AST
          </button>
          <button
            id="btn-show-dag"
            className={`ir-toggle-btn ${activeView === 'dag' ? 'ir-toggle-active ir-toggle-active-dag' : ''}`}
            onClick={() => setActiveView('dag')}
            title="Show Optimization DAG"
          >
            <Share2 style={{ width: 13, height: 13 }} />
            DAG
          </button>
        </div>
      </div>

      {/* ── View container ──────────────────────────────────────────────────── */}
      <div className="ir-view-container">

        {/* ── TAC View ──────────────────────────────────────────────────────── */}
        <div className={`ir-view ${activeView === 'tac' ? 'ir-view-visible' : 'ir-view-hidden'}`}>
          {irCode.length === 0 ? (
            <div className="empty-state">
              <TerminalSquare style={{ width: 40, height: 40, opacity: 0.25, marginBottom: '1rem' }} />
              <p>No Three-Address Code Generated</p>
              <p className="empty-state-subtext">
                Submit valid code to see TAC instructions.
              </p>
            </div>
          ) : (
            <div className="tac-code-block">
              <div className="tac-code-header">
                <Cpu style={{ width: 14, height: 14 }} />
                <span>Generated TAC — {irCode.length} instruction{irCode.length !== 1 ? 's' : ''}</span>
              </div>
              <div className="tac-code-lines">
                {irCode.map((line, index) => (
                  <div key={index} className="tac-line">
                    <span className="tac-line-num">{index + 1}</span>
                    <span className="tac-line-text">{line}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── AST View ────────────────────────────────────────────────────────── */}
        <div className={`ir-view ${activeView === 'ast' ? 'ir-view-visible' : 'ir-view-hidden'}`}>
          <ASTPanel
            astJson={astJson}
            astError={astError}
            hasSyntaxErrors={hasSyntaxErrors}
            hasSemanticErrors={hasSemanticErrors}
            isVisible={activeView === 'ast'}
          />
        </div>

        {/* ── DAG View ────────────────────────────────────────────────────────── */}
        <div className={`ir-view ${activeView === 'dag' ? 'ir-view-visible' : 'ir-view-hidden'}`}>
          <DAGPanel
            dagJson={dagJson}
            hasSyntaxErrors={hasSyntaxErrors}
            isVisible={activeView === 'dag'}
          />
        </div>

      </div>
    </div>
  );
}
