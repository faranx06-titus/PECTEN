import { useEffect, useState } from "react";
import { simulateCircuit } from "../services/api";

function AnalyzedCircuitSimulator({ analysis, imageUrl }) {
  const [resistance, setResistance] = useState(null);
  const [simulation, setSimulation] = useState(null);

  const circuit = analysis?.vision?.circuit;
  const solution = analysis?.solution;

  const resistor = circuit?.components?.find(
    (component) => component.type === "resistor"
  );

  const battery = circuit?.components?.find(
    (component) =>
      component.type === "battery" ||
      component.type === "cell"
  );

  useEffect(() => {
    if (resistor?.value != null) {
      setResistance(Number(resistor.value));
    }
  }, [resistor?.value]);

  useEffect(() => {
    if (resistance == null) return;

    const runSimulation = async () => {
      try {
        const result = await simulateCircuit(resistance);
        console.log("Simulation result:", result);
        setSimulation(result);
      } catch (error) {
        console.error("Simulation failed:", error);
      }
    };

    runSimulation();
  }, [resistance]);

  if (!circuit || !imageUrl) {
    return null;
  }

  const current =
    simulation?.total_current ??
    solution?.total_current ??
    0;

  const equivalentResistance =
    simulation?.equivalent_resistance ??
    solution?.equivalent_resistance ??
    resistance;

  const particleCount = Math.max(
  2,
  Math.min(12, Math.round(current * 2))
);

  return (
    <div
      style={{
        marginTop: "40px",
        padding: "20px",
        border: "1px solid #ddd",
        borderRadius: "12px",
        background: "#fafafa",
      }}
    >
      <h2>PECTEN Interactive Simulation</h2>

      <p>
        Battery:{" "}
        <strong>
          {battery?.value ?? "—"} {battery?.unit ?? "V"}
        </strong>
      </p>

      <p>
        Resistance:{" "}
        <strong>{resistance ?? "—"} Ω</strong>
      </p>

      <input
        type="range"
        min="1"
        max="20"
        step="1"
        value={resistance ?? 1}
        onChange={(event) => {
          setResistance(Number(event.target.value));
        }}
        style={{
          width: "300px",
        }}
      />

      <div style={{ marginTop: "15px" }}>
        <p>
          Equivalent Resistance:{" "}
          <strong>
            {equivalentResistance != null
              ? `${Number(equivalentResistance).toFixed(2)} Ω`
              : "—"}
          </strong>
        </p>

        <p>
          Current:{" "}
          <strong>
            {Number(current).toFixed(2)} A
          </strong>
        </p>
      </div>

      {/* ORIGINAL IMAGE + SIMULATION OVERLAY */}

      <div
        style={{
          position: "relative",
          width: "700px",
          maxWidth: "100%",
          marginTop: "25px",
          border: "2px solid #333",
          background: "white",
        }}
      >
        <img
          src={imageUrl}
          alt="Uploaded circuit"
          style={{
            display: "block",
            width: "100%",
            height: "auto",
          }}
        />

        {/* TEST ANIMATION OVERLAY */}

         <svg
    viewBox={`0 0 ${
      analysis.vision.visual.image_width
    } ${
      analysis.vision.visual.image_height
    }`}
    style={{
      position: "absolute",
      inset: 0,
      width: "100%",
      height: "100%",
      pointerEvents: "none",
    }}
  >
    {/* Gemini wire paths + animated current will go here */}
    {current > 0 &&
  analysis.vision.visual.wire_paths?.map((wire, index) => {
    const points = wire.points
      .map(([x, y]) => `${x},${y}`)
      .join(" ");

    const motionPath = wire.points
      .map(([x, y]) => `${x} ${y}`)
      .join(" L ");

    return (
      <g key={index}>
        {/* Highlight actual wire path */}
        <polyline
          points={points}
          fill="none"
          stroke="red"
          strokeWidth="16"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.35"
        />

        {/* Moving current particle */}
        {Array.from(
  { length: particleCount },
  (_, particle) => particle
).map((particle) => (
  <circle
    key={particle}
    r={Math.max(12, current * 6)}
    fill="red"
  >
    <animateMotion
      dur={`${Math.max(0.4, 4 / Math.max(current, 0.1))}s`}
      begin={`${particle * 0.4}s`}
      repeatCount="indefinite"
      path={`M ${motionPath}`}
    />
  </circle>
))}
      </g>
    );
  })}

<rect
  x="50"
  y="50"
  width="350"
  height="80"
  rx="12"
  fill="white"
  opacity="0.9"
/>

<text
  x="75"
  y="102"
  fontSize="36"
  fontWeight="bold"
  fill="red"
>
  Current: {Number(current).toFixed(2)} A
</text>
  </svg>
      </div>

      <div
        style={{
          marginTop: "25px",
          padding: "15px",
          background: "white",
          border: "1px solid #ddd",
          borderRadius: "10px",
        }}
      >
        <h3>Simulation Status</h3>

        <p>
          {current > 0
            ? "⚡ Current is flowing through the circuit."
            : "No current detected."}
        </p>
      </div>
    </div>
  );
}

export default AnalyzedCircuitSimulator;