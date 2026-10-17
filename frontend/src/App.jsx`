import { useState } from "react";
import {
  checkBackend,
  getDemoCircuit,
} from "./services/api";

import CircuitSimulator from "./components/CircuitSimulator";
import AnalyzedCircuitSimulator from "./components/AnalyzedCircuitSimulator";
import UploadQuestion from "./components/UploadQuestion";
import GeneratedCircuit from "./components/GeneratedCircuit";
import AnalysisToggle from "./components/AnalysisToggle";

function App() {
  const [status, setStatus] = useState("");
  const [circuit, setCircuit] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [mode, setMode] = useState("original");

  const testBackend = async () => {
    try {
      const data = await checkBackend();
      setStatus(data.status);
    } catch (error) {
      setStatus("Backend connection failed");
    }
  };

  const loadCircuit = async () => {
    try {
      const data = await getDemoCircuit();
      setCircuit(data);
    } catch (error) {
      console.error(error);
      setStatus("Circuit loading failed");
    }
  };

  const handleAnalysisComplete = (result, uploadedFile) => {
    setAnalysis(result);

    if (uploadedFile) {
      const imageUrl = URL.createObjectURL(uploadedFile);
      setUploadedImage(imageUrl);
    }
  };

  return (
    <div className="app-wrapper">
      <header className="header-section">
        <div className="brand-container">
          <span className="brand-logo">PECTEN</span>
          <span className="brand-tagline">Life to Textbooks.</span>
        </div>
        <div className="header-actions">
          <button className="btn-primary" onClick={testBackend}>
            Verify System
          </button>
          {status && <span className="status-badge">{status}</span>}
        </div>
      </header>

      <main className="dashboard-container">
        {/* Left Panel: Inputs */}
        <aside className="glass-panel">
          <h2>Input Center</h2>
          <p>Upload a circuit diagram to begin the reasoning process.</p>

          <div className="panel-content">
            <UploadQuestion onAnalysisComplete={handleAnalysisComplete} />

            <div className="demo-section" style={{ marginTop: '40px', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
              <h3>Fast Start</h3>
              <p>Test the engine with a pre-made circuit.</p>
              <button className="btn-primary" onClick={loadCircuit} style={{ width: '100%' }}>
                Load Demo Circuit
              </button>
            </div>
          </div>
        </aside>

        {/* Center Panel: Visualizer */}
        <section className="glass-panel center-stage">
          {uploadedImage && !analysis && (
            <div className="image-preview-container">
              <h3>Uploaded Diagram</h3>
              <img src={uploadedImage} alt="Uploaded circuit" className="full-width-img" />
            </div>
          )}

          {analysis && (
            <div className="simulation-wrapper">
              <AnalysisToggle mode={mode} setMode={setMode} />
              <div className="canvas-container">
                {mode === "original" && uploadedImage && (
                  <AnalyzedCircuitSimulator
                    analysis={analysis}
                    imageUrl={uploadedImage}
                  />
                )}
                {mode === "generated" && (
                  <GeneratedCircuit analysis={analysis} />
                )}
              </div>
            </div>
          )}

          {circuit && (
            <div className="demo-simulation">
              <h2>Demo Simulation</h2>
              <CircuitSimulator circuit={circuit} />
            </div>
          )}

          {!analysis && !circuit && (
            <div className="empty-state">
              <div className="empty-icon">⚡</div>
              <h3>No Circuit Loaded</h3>
              <p>Upload an image or load a demo to see the physics engine in action.</p>
            </div>
          )}
        </section>

        {/* Right Panel: Insights */}
        <aside className="glass-panel">
          <h2>Reasoning Engine</h2>

          {!analysis ? (
            <div className="placeholder-text">
              Waiting for analysis...
            </div>
          ) : (
            <div className="analysis-results">
              <div className="result-group">
                <div className="result-label">Problem Statement</div>
                <p className="problem-text">{analysis.vision?.problem?.text}</p>
              </div>

              <div className="result-group">
                <div className="result-label">Target Quantity</div>
                <div className="result-value">{analysis.vision?.problem?.asked_quantity || "Not specified"}</div>
              </div>

              <div className="result-group">
                <div className="result-label">Circuit Topology</div>
                <div className="result-value">{analysis.vision?.circuit?.type}</div>
              </div>

              <div className="result-group">
                <div className="result-label">Components Identified</div>
                <div className="component-list">
                  {analysis.vision?.circuit?.components?.map((comp) => (
                    <div key={comp.id} className="result-card">
                      <div className="card-header">
                        <strong>{comp.id}</strong>
                        <span className="comp-type">{comp.type}</span>
                      </div>
                      <div className="card-value">
                        {comp.value !== null ? `${comp.value} ${comp.unit}` : "Value not found"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {analysis.solution && (
                <div className="solution-summary">
                  <div className="result-label">Final Results</div>
                  <div className="result-card highlight">
                    <div className="result-label">Eq. Resistance</div>
                    <div className="result-value">{analysis.solution.equivalent_resistance} Ω</div>
                  </div>
                  <div className="result-card highlight">
                    <div className="result-label">Total Current</div>
                    <div className="result-value">{analysis.solution.total_current} A</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;
