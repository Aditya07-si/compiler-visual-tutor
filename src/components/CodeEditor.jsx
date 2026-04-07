import React from 'react';
import { Info } from 'lucide-react';

export function CodeEditor({ value, onChange, disabled }) {
  return (
    <div className="code-editor animate-fade-in">
      <textarea
        className="code-textarea"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        spellCheck="false"
        disabled={disabled}
      />
      <div className="code-editor-hint">
        <Info size={14} />
        <p style={{ margin: 0 }}>
          Paste source code here. The backend will perform lexical, syntax, and semantic analysis.
        </p>
      </div>
    </div>
  );
}
