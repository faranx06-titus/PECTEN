import { useEffect, useState } from "react";
import AnalyzedCircuitSimulator from "./components/AnalyzedCircuitSimulator";
import UploadQuestion from "./components/UploadQuestion";
import GeneratedCircuit from "./components/GeneratedCircuit";
import AnalysisToggle from "./components/AnalysisToggle";
import SettingsPanel from "./components/SettingsPanel";
import SimulationErrorBoundary from "./components/SimulationErrorBoundary";

const API_KEY_STORAGE = "pecten.geminiApiKey";

function getSavedApiKey() {
  try { return window.sessionStorage.getItem(API_KEY_STORAGE) || ""; }
  catch { return ""; }
}

function App() {
  const [analysis, setAnalysis] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [uploadedImage, setUploadedImage] = useState("");
  const [sourcePageImage, setSourcePageImage] = useState("");
  const [sourcePageError, setSourcePageError] = useState(false);
  const [documentInfo, setDocumentInfo] = useState(null);
  const [mode, setMode] = useState("original");
  const [topologyReviewed, setTopologyReviewed] = useState(false);
  const [apiKey, setApiKey] = useState(getSavedApiKey);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => () => {
    if (uploadedImage.startsWith("blob:")) URL.revokeObjectURL(uploadedImage);
  }, [uploadedImage]);

  useEffect(() => () => {
    if (sourcePageImage.startsWith("blob:")) URL.revokeObjectURL(sourcePageImage);
  }, [sourcePageImage]);

  const handleAnalysisComplete = (result, pageImage, sourcePage, info) => {
    setAnalysis(result);
    setSimulationResult(result.solution ?? null);
    setTopologyReviewed(false);
    setMode("original");
    setUploadedImage(URL.createObjectURL(pageImage));
    setSourcePageImage(URL.createObjectURL(sourcePage));
    setSourcePageError(false);
    setDocumentInfo(info);
  };

  const startOver = () => {
    setAnalysis(null);
    setSimulationResult(null);
    setUploadedImage("");
    setSourcePageImage("");
    setDocumentInfo(null);
    setTopologyReviewed(false);
  };

  const saveApiKey = (key) => {
    setApiKey(key);
    try { window.sessionStorage.setItem(API_KEY_STORAGE, key); } catch { /* Keep the key in memory for this page. */ }
  };

  const clearApiKey = () => {
    setApiKey("");
    try { window.sessionStorage.removeItem(API_KEY_STORAGE); } catch { /* The in-memory key is still cleared. */ }
  };

  const hasMultipleSources = (analysis?.vision?.circuit?.components ?? [])
    .filter((component) => ["battery", "cell"].includes(component.type)).length > 1;

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="wordmark" href="#home" onClick={(event) => { event.preventDefault(); startOver(); }} aria-label="PECTEN home">PECTEN</a>
        <span className="header-description">A clearer way to explore physics</span>
        <div className="header-actions">
          {analysis && <button type="button" className="quiet-button" onClick={startOver}>New question</button>}
          <button type="button" className="quiet-button" onClick={() => setSettingsOpen(true)}>Settings</button>
        </div>
      </header>

      {!analysis ? (
        <main className="home-page">
          <UploadQuestion onAnalysisComplete={handleAnalysisComplete} apiKey={apiKey} onOpenSettings={() => setSettingsOpen(true)} />
          <section className="how-it-works" aria-label="How PECTEN works">
            <article><span>01</span><div><strong>Choose a page</strong><p>Upload a worksheet, textbook PDF, or circuit image.</p></div></article>
            <article><span>02</span><div><strong>Ask your question</strong><p>Paste the problem or let PECTEN read it from the page.</p></div></article>
            <article><span>03</span><div><strong>Explore the physics</strong><p>Review the circuit, check its connections, and change values.</p></div></article>
          </section>
          <p className="home-footnote">Circuit support: series, parallel, mixed, and bridge networks with batteries/cells and known resistor or bulb values.</p>
        </main>
      ) : (
        <main className="workspace-page">
          <div className="workspace-titlebar">
            <div>
              <p className="section-kicker">YOUR PHYSICS WORKSPACE</p>
              <h1>{documentInfo?.fileName || "Circuit analysis"}{documentInfo?.pageNumber ? <span> · Page {documentInfo.pageNumber}</span> : null}</h1>
              {documentInfo?.question && <p className="workspace-question">“{documentInfo.question}”</p>}
            </div>
            <button type="button" className="quiet-button" onClick={startOver}>Choose another page</button>
          </div>

          <div className="workspace-grid">
            <section className="document-panel">
              <div className="panel-heading"><div><p className="section-kicker">SOURCE PAGE</p><h2>Original question</h2></div></div>
              <div className="document-page-frame">
                <div className="document-page-visual">
                  <img src={sourcePageImage} alt="Selected page from the uploaded document" onError={() => setSourcePageError(true)} />
                  {sourcePageError && <p className="image-error-message" role="alert">The analysis succeeded, but this browser could not display the original page image.</p>}
                  {documentInfo?.cropRect && <div className="document-crop-marker" style={{
                    left: `${documentInfo.cropRect.x * 100}%`, top: `${documentInfo.cropRect.y * 100}%`,
                    width: `${documentInfo.cropRect.width * 100}%`, height: `${documentInfo.cropRect.height * 100}%`,
                  }} />}
                </div>
              </div>
              <div className="question-readback">
                <span>Question PECTEN is working on</span>
                <p>{analysis.vision?.problem?.text || documentInfo?.question || "No question text was detected. Check the circuit and values before starting."}</p>
              </div>
            </section>

            <section className="simulation-panel">
              <div className="simulation-panel-heading">
                <div><p className="section-kicker">CIRCUIT MODEL</p><h2>Reasoning and simulation</h2></div>
                <AnalysisToggle mode={mode} setMode={setMode} generatedDisabled={!topologyReviewed || hasMultipleSources}
                  generatedDisabledReason={hasMultipleSources ? "The generated model view shows one source; use the original diagram overlay for multi-source circuits." : undefined} />
              </div>
              <SimulationErrorBoundary key={`${uploadedImage}-${mode}`} onReset={startOver}>
                {mode === "original" && <AnalyzedCircuitSimulator
                  analysis={analysis}
                  imageUrl={uploadedImage}
                  onSimulationChange={setSimulationResult}
                  topologyReviewed={topologyReviewed}
                  onTopologyReviewedChange={setTopologyReviewed}
                />}
                {mode === "generated" && <GeneratedCircuit analysis={analysis} simulation={simulationResult} />}
              </SimulationErrorBoundary>
              {analysis.simulation_error && <div className="review-callout" role="status">
                <strong>The first circuit reading needs a check.</strong>
                <p>{analysis.simulation_error} Review the highlighted component values and connections before starting the simulation.</p>
              </div>}
              <section className="identified-components">
                <p className="section-kicker">READ FROM THE PAGE</p>
                <h3>Detected components</h3>
                <div className="component-chips">
                  {(analysis.vision?.circuit?.components || []).map((component) => (
                    <span key={component.id}><b>{component.id}</b> {component.type}{component.value != null ? ` · ${component.value} ${component.unit || ""}` : " · value not found"}</span>
                  ))}
                </div>
              </section>
            </section>
          </div>
        </main>
      )}

      {settingsOpen && <SettingsPanel open onClose={() => setSettingsOpen(false)} hasSavedKey={Boolean(apiKey)} onSave={saveApiKey} onClear={clearApiKey} />}
    </div>
  );
}

export default App;
