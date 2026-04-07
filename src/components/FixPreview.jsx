import React from 'react';
import { Lightbulb, Code2 } from 'lucide-react';

export function FixPreview({ fixedCode, explanation }) {
  if (!fixedCode && !explanation) {
    return (
      <div className="empty-state animate-fade-in">
        <Lightbulb size={48} strokeWidth={1.5} />
        <p>No fixes available</p>
        <p className="empty-state-subtext">
          After analysis, this area will show the corrected code and a human-friendly explanation of
          what was fixed and why.
        </p>
      </div>
    );
  }

  return (
    <div className="fix-preview animate-fade-in">
      {explanation && (
        <div className="fix-explanation-container">
          <Lightbulb className="fix-info-icon" />
          <p className="fix-explanation">{explanation}</p>
        </div>
      )}

      {fixedCode && (
        <div className="fixed-code-container">
          <div className="fixed-code-header">
            <Code2 size={14} />
            <span>Suggested Fix</span>
          </div>
          <pre className="fixed-code-block">
            <code>{fixedCode}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
