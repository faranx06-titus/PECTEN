import { useEffect, useState } from "react";
import { simulateCircuit } from "../services/api";
function CircuitSimulator({ circuit }) {
  const [r1Resistance, setR1Resistance] = useState(2);
  const [previousResistance, setPreviousResistance] =
  useState(2);
  const [simulation, setSimulation] = useState(null);
  const updateCircuit = async (resistance) => {
  try {
    const result = await simulateCircuit(resistance);

    setSimulation(result);
  } catch (error) {
    console.error("Circuit simulation failed:", error);
  }
};
useEffect(() => {
  updateCircuit(r1Resistance);
}, []);

  if (!circuit) {
    return null;
  }

  const r1 = circuit.components.find(
    (component) => component.id === "R1"
  );

  const r2 = circuit.components.find(
    (component) => component.id === "R2"
  );

  const r3 = circuit.components.find(
    (component) => component.id === "R3"
  );
  const r2Result = simulation?.components?.R2;
  const r3Result = simulation?.components?.R3;
  const r1Result = simulation?.components?.R1;

  const totalCurrent =
  simulation?.total_current || 0;
  const explanation = simulation
  ? previousResistance < r1Resistance
    ? `
You increased R1 from ${previousResistance} Ω to ${r1Resistance} Ω.

This increased the total circuit resistance to
${simulation.equivalent_resistance.toFixed(2)} Ω.

According to Ohm's Law, increasing resistance reduces current.

The total current is now
${simulation.total_current.toFixed(2)} A.

Because less current flows through the circuit,
the bulbs become dimmer.
`
    : previousResistance > r1Resistance
    ? `
You decreased R1 from ${previousResistance} Ω to ${r1Resistance} Ω.

This reduced the total circuit resistance.

According to Ohm's Law, lower resistance allows more current to flow.

The total current is now
${simulation.total_current.toFixed(2)} A.

Because more current flows through the bulbs,
they become brighter.
`
    : `
No circuit changes detected.
`
  : "";

const animationDuration =
  totalCurrent > 0
    ? Math.max(0.15, 1 / totalCurrent)
    : 0;

const wireStyle = {
  animation:
    totalCurrent > 0
      ? `currentFlow ${animationDuration}s linear infinite`
      : "none",
};

 
   

  return (
    <div style={{ marginTop: "30px" }}>
      <h2>PECTEN Simulation</h2>
      <div style={{ marginBottom: "20px" }}>
  <label>
    R1 Resistance:{" "}
    <strong>{r1Resistance} Ω</strong>
  </label>

  <br />

  <input
    type="range"
    min="1"
    max="10"
    step="1"
    value={r1Resistance}
    onChange={(event) => {
  const resistance = Number(event.target.value);

  setPreviousResistance(r1Resistance);

  setR1Resistance(resistance);

  updateCircuit(resistance);
}}
     
  />

   <p>
  Total Resistance:{" "}
  {simulation
    ? `${simulation.equivalent_resistance.toFixed(2)} Ω`
    : "—"}
</p>

<p>
  Total Current:{" "}
  {simulation
    ? `${simulation.total_current.toFixed(2)} A`
    : "—"}
</p>
</div>


      <svg
        width="700"
        height="400"
        

        viewBox="0 0 700 400"
        style={{
          border: "1px solid #ccc",
          background: "#fafafa",
        }}
      >
        <defs>
  <style>
    {`
      @keyframes currentFlow {
        from {
          stroke-dashoffset: 0;
        }
        to {
          stroke-dashoffset: -40;
        }
      }
    `}
  </style>
</defs>
         

        {/* ========================= */}
        {/* WIRES */}
        {/* ========================= */}

        {/* Battery → R1 */}
         <line
  x1="100"
  y1="200"
  x2="220"
  y2="200"
  stroke="black"
  strokeWidth="4"
  strokeDasharray="10 10"
  style={wireStyle}
/>

        {/* R1 → parallel junction */}
        <line
          x1="280"
          y1="200"
          x2="400"
          y2="200"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
          style={wireStyle}
        />

        {/* Top branch */}
        <line
          x1="400"
          y1="200"
          x2="400"
          y2="100"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        <line
          x1="400"
          y1="100"
          x2="500"
          y2="100"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        <line
          x1="560"
          y1="100"
          x2="600"
          y2="100"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        <line
          x1="600"
          y1="100"
          x2="600"
          y2="300"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        {/* Bottom branch */}
        <line
          x1="400"
          y1="200"
          x2="400"
          y2="300"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        <line
          x1="400"
          y1="300"
          x2="500"
          y2="300"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        <line
          x1="560"
          y1="300"
          x2="600"
          y2="300"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        {/* Return wire */}
        <line
          x1="600"
          y1="300"
          x2="600"
          y2="200"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        <line
          x1="600"
          y1="200"
          x2="100"
          y2="200"
          stroke="black"
          strokeWidth="4"
          strokeDasharray="10 10"
style={wireStyle}
        />

        {/* ========================= */}
        {/* BATTERY */}
        {/* ========================= */}

        <line
          x1="80"
          y1="170"
          x2="80"
          y2="230"
          stroke="black"
          strokeWidth="6"
        />

        <line
          x1="100"
          y1="180"
          x2="100"
          y2="220"
          stroke="black"
          strokeWidth="3"
        />

        <text
          x="55"
          y="150"
          fontSize="18"
        >
          🔋 {circuit.battery.voltage}V
        </text>

        {/* ========================= */}
        {/* R1 */}
        {/* ========================= */}

        <rect
          x="220"
          y="180"
          width="60"
          height="40"
          fill="white"
          stroke="black"
          strokeWidth="3"
        />

        <text
          x="235"
          y="207"
          fontSize="16"
        >
          R1
        </text>

        {/* ========================= */}
        {/* BULB R2 */}
        {/* ========================= */}

         <circle
  cx="530"
  cy="100"
  r="30"
  fill="white"
  stroke="black"
  strokeWidth="3"
  style={{
  filter: `drop-shadow(
    0 0 ${Math.min((r2Result?.power || 0) * 1.5, 30)}px
    rgba(255, 200, 0, 0.9)
  )`,
}}
/>

        <text
          x="515"
          y="106"
          fontSize="16"
        >
          💡
        </text>

        {/* ========================= */}
        {/* BULB R3 */}
        {/* ========================= */}

        <circle
  cx="530"
  cy="300"
  r="30"
  fill="white"
  stroke="black"
  strokeWidth="3"
  style={{
  filter: `drop-shadow(
    0 0 ${Math.min((r3Result?.power || 0) * 1.5, 30)}px
    rgba(255, 200, 0, 0.9)
  )`,
}}
/>

        <text
          x="515"
          y="306"
          fontSize="16"
        >
          💡
        </text>

        {/* ========================= */}
        {/* LABELS */}
        {/* ========================= */}

        <text
          x="500"
          y="60"
          fontSize="16"
        >
          R2: {r2Result?.current?.toFixed(2) || "—"} A
        </text>

        <text
          x="500"
          y="360"
          fontSize="16"
        >
          R3: {r3Result?.current?.toFixed(2) || "—"} A
        </text>

        <text
          x="220"
          y="160"
          fontSize="16"
        >
          I = {r1Result?.current?.toFixed(2) || "—"} A
        </text>

      </svg>

      {/* ========================= */}
      {/* RESULTS */}
      {/* ========================= */}

      <div style={{ marginTop: "20px" }}>
        <h3>Component Results</h3>

        {circuit.components.map((component) => (
          <div key={component.id}>
            <strong>{component.id}</strong>{" "}
            {circuit.components.map((component) => {
          const result =
            simulation?.components?.[component.id];

  return (
    <div key={component.id}>
      <strong>{component.id}</strong>{" "}
      | I = {result?.current?.toFixed(2) || "—"} A{" "}
      | V = {result?.voltage?.toFixed(2) || "—"} V{" "}
      | P = {result?.power?.toFixed(2) || "—"} W
    </div>
     
  
     
  );
})}
             
          </div>
        ))}
      </div>
      <div
  style={{
    marginTop: "30px",
    padding: "15px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    background: "#fffdf5",
  }}
>
  <h3>AI Reasoning</h3>
   

  <pre
    style={{
      whiteSpace: "pre-wrap",
      fontFamily: "inherit",
    }}
  >
    {explanation}
  </pre>
</div>
    </div>
  );
}

export default CircuitSimulator;