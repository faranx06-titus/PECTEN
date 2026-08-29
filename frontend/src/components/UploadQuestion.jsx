import { useState } from "react";
import { analyzeCircuit } from "../services/api";

function UploadQuestion({ onAnalysisComplete }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    if (!selectedFile) {
      return;
    }

    setFile(selectedFile);
    setError("");
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please select a circuit image first.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const result = await analyzeCircuit(file);

      console.log("PECTEN analysis:", result);
      console.log(
  "WIRE PATH COORDINATES:",
  JSON.stringify(
    result.vision?.visual?.wire_paths,
    null,
    2
  )
);

      if (onAnalysisComplete) {
        onAnalysisComplete(result, file);
      }
    } catch (error) {
      console.error("Circuit analysis failed:", error);
      setError("Failed to analyze the circuit.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: "30px" }}>
      <h2>Upload Physics Question</h2>

      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
      />

      {file && (
        <p>
          Selected: <strong>{file.name}</strong>
        </p>
      )}

      <button
        onClick={handleAnalyze}
        disabled={!file || loading}
      >
        {loading ? "Analyzing..." : "Analyze Circuit"}
      </button>

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}
    </div>
  );
}

export default UploadQuestion;