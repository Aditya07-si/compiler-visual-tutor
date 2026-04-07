import React from 'react';
import { Play, Sparkles } from 'lucide-react';

export function TopBar({ onAnalyze, isAnalyzing }) {
  return (
    <header className="topbar animate-fade-in">
      <div className="topbar-left">
        <div className="logo-container">
          <Sparkles size={20} />
        </div>
        <div>
          <h1 className="topbar-title">Compiler Visual Tutor</h1>
          <p className="topbar-subtitle">Learn compiler errors with guided visual explanations</p>
        </div>
      </div>
      <div className="topbar-right">
        <button
          className="primary-button"
          type="button"
          onClick={onAnalyze}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? (
            <>
              <Play className="button-icon spinning" /> Analyzing…
            </>
          ) : (
            <>
              <Play className="button-icon" /> Analyze Code
            </>
          )}
        </button>
      </div>
    </header>
  );
}
