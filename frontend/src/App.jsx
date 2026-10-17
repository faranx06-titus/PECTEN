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
  console.log("Analysis received:", result);
  console.log("Original image:", uploadedFile);

  setAnalysis(result);

  if (uploadedFile) {
    const imageUrl = URL.createObjectURL(uploadedFile);
    console.log("Image URL:", imageUrl);
    setUploadedImage(imageUrl);
  }
};

  return (
    <div>
      <h1>PECTEN</h1>
      <p>Life to Textbooks.</p>

      {/* Backend test */}
      <button onClick={testBackend}>
        Test Backend
      </button>

      <p>{status}</p>

      {/* NEW: Upload Question */}
      <UploadQuestion
        onAnalysisComplete={handleAnalysisComplete}
      />
      {uploadedImage && (
  <div style={{ marginTop: "20px" }}>
    <h3>Original Uploaded Image</h3>

    <img
      src={uploadedImage}
      alt="Uploaded circuit"
      style={{
        maxWidth: "700px",
        width: "100%",
        display: "block",
        border: "2px solid black",
      }}
    />
  </div>
)}

      {/* Show AI analysis */}
      {analysis && (
        <div style={{ marginTop: "30px" }}>
          <h2>PECTEN Analysis</h2>

          <h3>Problem</h3>

          <p>
            {analysis.vision?.problem?.text}
          </p>

          <p>
            Asked quantity:{" "}
            <strong>
              {analysis.vision?.problem?.asked_quantity}
            </strong>
          </p>

          <h3>Circuit</h3>

          <p>
            Type:{" "}
            <strong>
              {analysis.vision?.circuit?.type}
            </strong>
          </p>

          <h3>Components</h3>

          {analysis.vision?.circuit?.components?.map(
            (component) => (
              <div key={component.id}>
                <strong>{component.id}</strong>{" "}
                — {component.type}{" "}
                {component.value !== null &&
                  `(${component.value} ${component.unit})`}
              </div>
            )
          )}

          <h3>Solution</h3>

          {analysis.solution && (
            <div>
              <p>
                Equivalent Resistance:{" "}
                {analysis.solution.equivalent_resistance} Ω
              </p>

              <p>
                Total Current:{" "}
                {analysis.solution.total_current} A
              </p>
            </div>
          )}
        </div>
      )}
      {analysis && (
  <div style={{ marginTop: "30px" }}>
    <AnalysisToggle mode={mode} setMode={setMode} />

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
)}
                
           
      {/* Existing demo circuit */}
      <div style={{ marginTop: "40px" }}>
        <button onClick={loadCircuit}>
          Load Demo Circuit
        </button>

        {circuit && (
          <div>
            <h2>Demo Circuit</h2>

            <p>
              Battery: {circuit.battery.voltage}
              {circuit.battery.unit}
            </p>

            {circuit.components.map((component) => (
              <div key={component.id}>
                <h3>
                  {component.type}: {component.id}
                </h3>

                <p>
                  Resistance: {component.resistance} Ω
                </p>

                <p>
                  Current: {component.current} A
                </p>

                <p>
                  Voltage: {component.voltage} V
                </p>

                <p>
                  Power: {component.power} W
                </p>
              </div>
            ))}

            <CircuitSimulator circuit={circuit} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;