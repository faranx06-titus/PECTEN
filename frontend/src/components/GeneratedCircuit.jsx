import React from "react";

function GeneratedCircuitAI({ analysis }) {
  const solution = analysis?.solution || {};
  const circuit = analysis?.vision?.circuit || {};
  const visual = analysis?.vision?.visual || {};

  const components = circuit.components || [];
  const wires = visual.wire_paths || [];

  const current = Number(solution.total_current || 0);
  const resistance = Number(solution.equivalent_resistance || 0);
  const voltage = Number(solution.voltage || 0);
  const power = Number(solution.power || voltage * current || 0);

  const battery = components.find(c => c.type === "battery");
  const resistors = components.filter(c => c.type === "resistor");

  const makePath = (points = []) =>
    points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`)
      .join(" ");

  return (
    <div style={{ marginTop: 30 }}>
      <h2>Generated AI Circuit</h2>

      <svg
        viewBox={`0 0 ${visual.image_width || 700} ${visual.image_height || 400}`}
        style={{
          width: "100%",
          maxWidth: 700,
          border: "1px solid #ccc",
          background: "#fff"
        }}
      >
        {/* AI Wire Paths */}
        {wires.map((wire, index) => (
          <path
            key={index}
            d={makePath(wire.points)}
            fill="none"
            stroke="#222"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}

        {/* Battery */}
        {battery?.visual?.bbox && (() => {
          const [x1, y1, x2, y2] = battery.visual.bbox;
          const cx = (x1 + x2) / 2;

          return (
            <g>
              <line
                x1={cx - 8}
                y1={y1}
                x2={cx - 8}
                y2={y2}
                stroke="black"
                strokeWidth="5"
              />
              <line
                x1={cx + 8}
                y1={y1 + 8}
                x2={cx + 8}
                y2={y2 - 8}
                stroke="black"
                strokeWidth="2"
              />

              <text
                x={cx}
                y={y1 - 10}
                textAnchor="middle"
                fontSize="11"
              >
                {battery.value || voltage} V
              </text>
            </g>
          );
        })()}

        {/* Resistors */}
        {resistors.map((r) => {
          const box = r.visual?.bbox;
          if (!box) return null;

          const [x1, y1, x2, y2] = box;
          const cx = (x1 + x2) / 2;
          const cy = (y1 + y2) / 2;

          const result = solution.components?.[r.id];

          return (
            <g key={r.id}>
              <rect
                x={x1}
                y={y1}
                width={x2 - x1}
                height={y2 - y1}
                rx="4"
                fill="white"
                stroke="black"
                strokeWidth="2"
              />

              <text
                x={cx}
                y={cy - 6}
                textAnchor="middle"
                fontSize="11"
                fontWeight="bold"
              >
                {r.id}
              </text>

              <text
                x={cx}
                y={cy + 6}
                textAnchor="middle"
                fontSize="10"
              >
                {r.value} Ω
              </text>

              <text
                x={cx}
                y={cy + 18}
                textAnchor="middle"
                fontSize="9"
                fill="#2563eb"
              >
                {result?.current?.toFixed(2) || "0.00"} A
              </text>
            </g>
          );
        })}

        {/* Animated Current */}
        {wires[0]?.points && (
          <circle r="6" fill="red">
            <animateMotion
              dur={current > 0 ? `${Math.max(0.8, 3 / current)}s` : "2s"}
              repeatCount="indefinite"
              path={makePath(wires[0].points)}
            />
          </circle>
        )}
      </svg>

      <div style={{ marginTop: 20 }}>
        <h3>Calculated Values</h3>

        <p><strong>Type:</strong> {circuit.type}</p>
        <p><strong>Equivalent Resistance:</strong> {resistance} Ω</p>
        <p><strong>Total Voltage:</strong> {voltage} V</p>
        <p><strong>Total Current:</strong> {current.toFixed(2)} A</p>
        <p><strong>Total Power:</strong> {power.toFixed(2)} W</p>
      </div>

      <div style={{ marginTop: 25 }}>
        <h3>Component Results</h3>

        {resistors.map((r) => {
          const result = solution.components?.[r.id];

          return (
            <div
              key={r.id}
              style={{
                padding: 10,
                border: "1px solid #ddd",
                borderRadius: 8,
                marginBottom: 8
              }}
            >
              <strong>{r.id}</strong> ({r.value} Ω)

              <div>Current: {result?.current?.toFixed(2) || "0.00"} A</div>
              <div>Voltage: {result?.voltage?.toFixed(2) || "0.00"} V</div>
              <div>Power: {result?.power?.toFixed(2) || "0.00"} W</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default GeneratedCircuitAI;