function AnalysisToggle({ mode, setMode }) {
  return (
    <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
      <button
        onClick={() => setMode("original")}
        style={{
          padding: "10px 18px",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          background: mode === "original" ? "#2563eb" : "#e5e7eb",
          color: mode === "original" ? "#fff" : "#000",
          fontWeight: "600",
        }}
      >
        Original Analysis
      </button>

      <button
        onClick={() => setMode("generated")}
        style={{
          padding: "10px 18px",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          background: mode === "generated" ? "#16a34a" : "#e5e7eb",
          color: mode === "generated" ? "#fff" : "#000",
          fontWeight: "600",
        }}
      >
        Generated Analysis
      </button>
    </div>
  );
}

export default AnalysisToggle;