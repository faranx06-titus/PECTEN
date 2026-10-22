function AnalysisToggle({ mode, setMode, generatedDisabled = false, generatedDisabledReason }) {
  return (
    <div className="analysis-toggle" role="tablist" aria-label="Circuit view">
      <button
        type="button"
        role="tab"
        aria-selected={mode === "original"}
        onClick={() => setMode("original")}
        className={mode === "original" ? "is-active" : ""}
      >
        Diagram overlay
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={mode === "generated"}
        onClick={() => setMode("generated")}
        disabled={generatedDisabled}
        title={generatedDisabled ? (generatedDisabledReason || "Review and confirm the detected topology first") : undefined}
        className={mode === "generated" ? "is-active" : ""}
      >
        Circuit model
      </button>
    </div>
  );
}

export default AnalysisToggle;
