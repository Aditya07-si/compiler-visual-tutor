import React from 'react';
import { Zap, ListChecks } from 'lucide-react';

export function OptimizePanel({ optimizedCode = [], optimizations = [] }) {
    if (!optimizedCode || optimizedCode.length === 0) {
        return (
            <div className="empty-state">
                <Zap style={{ width: 40, height: 40, opacity: 0.25, marginBottom: '1rem' }} />
                <p>No Optimizations Applied</p>
                <p className="empty-state-subtext">
                    Submit code that generates valid IR to see optimization details.
                </p>
            </div>
        );
    }

    return (
        <div className="opt-panel">
            {/* Optimizations log */}
            {optimizations.length > 0 && (
                <div className="opt-log-box">
                    <div className="opt-log-header">
                        <ListChecks style={{ width: 14, height: 14 }} />
                        Optimizations Log
                    </div>
                    <ul className="opt-log-list">
                        {optimizations.map((opt, i) => (
                            <li key={i} className="opt-log-item">
                                <span className="opt-log-bullet">•</span>
                                {opt}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {optimizations.length === 0 && (
                <div className="opt-log-box opt-log-empty">
                    <div className="opt-log-header">
                        <ListChecks style={{ width: 14, height: 14 }} />
                        Optimizations Log
                    </div>
                    <p className="opt-log-none">No safe optimizations could be applied.</p>
                </div>
            )}

            {/* Optimized IR code */}
            <div className="tac-code-block" style={{ flex: 1, minHeight: 0 }}>
                <div className="tac-code-header" style={{ color: '#86efac', background: 'rgba(34,197,94,0.1)', borderColor: 'rgba(34,197,94,0.2)' }}>
                    <Zap style={{ width: 14, height: 14 }} />
                    <span>Optimized IR</span>
                </div>
                <div className="tac-code-lines">
                    {optimizedCode.map((line, index) => (
                        <div key={index} className="tac-line">
                            <span className="tac-line-num">{index + 1}</span>
                            <span className="tac-line-text">{line}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
