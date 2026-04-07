import React from 'react';
import { AlertCircle, AlertTriangle, TerminalSquare } from 'lucide-react';

function ErrorBadge({ severity }) {
  if (severity === 'warning') {
    return <span className="badge badge-warning">Warning</span>;
  }
  return <span className="badge badge-error">Error</span>;
}

function StatusBadge({ isFixed }) {
  if (isFixed) {
    return <span className="badge badge-success">Auto-Fixed</span>;
  }
  return <span className="badge badge-neutral">Manual Fix Required</span>;
}

export function ErrorPanel({ errors }) {
  if (!errors || errors.length === 0) {
    return (
      <div className="empty-state animate-fade-in">
        <AlertCircle size={48} strokeWidth={1.5} />
        <p>No errors detected</p>
        <p className="empty-state-subtext">
          Run analysis to see lexical, syntax, and semantic errors highlighted here.
        </p>
      </div>
    );
  }

  return (
    <div className="error-list">
      {errors.map((err, index) => (
        <article
          key={err.id}
          className={`error-card animate-fade-in ${err.severity === 'warning' ? 'warning' : ''}`}
          style={{ animationDelay: `${index * 0.1}s` }}
        >
          <div className="error-card-header">
            {err.severity === 'warning' ? (
              <AlertTriangle className="error-icon" />
            ) : (
              <AlertCircle className="error-icon" />
            )}
            <span className="error-type">{err.type}</span>
            <span className="error-location">
              Line {err.line}, Col {err.column}
            </span>
            <div className="error-badges">
              <ErrorBadge severity={err.severity} />
              {err.recovery_method && err.recovery_method !== "None" && (
                 <span className="badge badge-neutral">{err.recovery_method}</span>
              )}
              {err.suggestion !== undefined && err.suggestion !== null && (
                <StatusBadge isFixed={err.auto_corrected} />
              )}
            </div>
          </div>
          <p className="error-message">{err.message}</p>
          {err.hint && (
            <div className="error-hint">
              <SparklesIcon />
              <div className="error-hint-content">
                <span>{err.hint}</span>
                {err.suggestion && !err.auto_corrected && (
                  <span className="error-suggestion"> Suggested: {err.suggestion}</span>
                )}
              </div>
            </div>
          )}
          {err.code && (
            <p className="error-code">
              <TerminalSquare size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
              {err.code}
            </p>
          )}
        </article>
      ))}
    </div>
  );
}

function SparklesIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: '2px' }}>
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}
