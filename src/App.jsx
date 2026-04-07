import React, { useState } from 'react';
import { FileCode2, ShieldAlert, Wand2 } from 'lucide-react';
import { CodeEditor } from './components/CodeEditor.jsx';
import { ErrorPanel } from './components/ErrorPanel.jsx';
import { FixPreview } from './components/FixPreview.jsx';
import { TopBar } from './components/TopBar.jsx';
import { IRPanel } from './components/IRPanel.jsx';
import { OptimizePanel } from './components/OptimizePanel.jsx';

const SAMPLE_CODE = `int main() {
  printf("Hello world")
  return 0
}`;

export default function App() {
  const [sourceCode, setSourceCode] = useState(SAMPLE_CODE);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errors, setErrors] = useState([]);
  const [fixedCode, setFixedCode] = useState('');
  const [explanation, setExplanation] = useState('');
  const [intermediateCode, setIntermediateCode] = useState([]);
  const [optimizedCode, setOptimizedCode] = useState([]);
  const [optimizationsApplied, setOptimizationsApplied] = useState([]);
  // ── AST state ─────────────────────────────────────────────────────────────
  const [astJson, setAstJson] = useState(null);
  const [astError, setAstError] = useState(null);
  // ── DAG state ─────────────────────────────────────────────────────────────
  const [dagJson, setDagJson] = useState(null);

  async function handleAnalyze() {
    setIsAnalyzing(true);
    // Reset previous results
    setAstJson(null);
    setAstError(null);
    setDagJson(null);

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: 'c',
          source_code: sourceCode
        })
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();

      setErrors(
        (data.errors || []).map((err, index) => ({
          id: index + 1,
          severity: 'error',
          ...err
        }))
      );
      setFixedCode(data.fixed_code || '');
      setExplanation(data.explanation || '');
      setIntermediateCode(data.intermediate_code || []);
      setOptimizedCode(data.optimized_code || []);
      setOptimizationsApplied(data.optimizations_applied || []);
      // ── AST from pipeline ────────────────────────────────────────────────
      setAstJson(data.ast_json || null);
      setAstError(data.ast_error || null);
      // ── DAG from pipeline ────────────────────────────────────────────────
      setDagJson(data.dag_json || null);

    } catch (err) {
      console.error('Failed to analyze code', err);
      setErrors([
        {
          id: 1,
          type: 'Connection Error',
          code: 'BACKEND_UNAVAILABLE',
          message: 'Could not reach the analysis backend.',
          line: 0,
          column: 0,
          hint: 'Make sure the FastAPI server is running on http://localhost:8000.',
          severity: 'error'
        }
      ]);
      setFixedCode('');
      setExplanation('The frontend could not connect to the backend. Start the FastAPI server and try again.');
      setIntermediateCode([]);
      setOptimizedCode([]);
      setOptimizationsApplied([]);
      setAstJson(null);
      setAstError(null);
      setDagJson(null);
    } finally {
      setIsAnalyzing(false);
    }
  }

  // Separate syntax vs semantic error flags for AST panel rendering
  const hasSyntaxErrors = errors.some(
    e => (e.type === 'Lexical Error' || e.type === 'Syntax Error') && !e.auto_corrected
  );
  const hasSemanticErrors = errors.some(
    e => e.type === 'Semantic Error'
  );

  return (
    <div className="app-root">
      <TopBar onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
      <main className="app-main">
        <section className="pane pane-left animate-fade-in" style={{ animationDelay: '0s' }}>
          <div className="pane-header">
            <FileCode2 className="pane-icon" />
            <h2 className="pane-title">Source Code</h2>
          </div>
          <CodeEditor value={sourceCode} onChange={setSourceCode} disabled={isAnalyzing} />
        </section>

        <section className="pane pane-middle animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="pane-header">
            <ShieldAlert className="pane-icon" />
            <h2 className="pane-title">Analysis</h2>
          </div>
          <ErrorPanel errors={errors} />
        </section>

        <section className="pane pane-right animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="pane-header">
            <Wand2 className="pane-icon" />
            <h2 className="pane-title">Preview &amp; Fixes</h2>
          </div>
          <FixPreview fixedCode={fixedCode} explanation={explanation} />
        </section>

        {/* ── Bottom-left: IR (TAC + AST + DAG toggle) ─────────────────────── */}
        <section className="pane pane-bottom-left animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <IRPanel
            irCode={intermediateCode}
            astJson={astJson}
            astError={astError}
            dagJson={dagJson}
            hasSyntaxErrors={hasSyntaxErrors}
            hasSemanticErrors={hasSemanticErrors}
          />
        </section>

        <section className="pane pane-bottom-right animate-fade-in" style={{ animationDelay: '0.4s' }}>
          <OptimizePanel optimizedCode={optimizedCode} optimizations={optimizationsApplied} />
        </section>
      </main>
    </div>
  );
}
