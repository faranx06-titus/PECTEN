function GeneratedCircuitAI({ analysis, simulation }) {
  const solution = simulation || analysis?.solution || {};
  const circuit = analysis?.vision?.circuit || {};
  const visual = analysis?.vision?.visual || {};

  const components = circuit.components || [];
  const wires = visual.wire_paths || [];

  const current = Number(solution.total_current || 0);
  const resistance = Number(solution.equivalent_resistance || 0);
  const voltage = Number(solution.voltage || 0);
  const power = Number(solution.power || voltage * current || 0);

  const battery = components.find(c => c.type === "battery" || c.type === "cell");
  const resistors = components.filter(c => c.type === "resistor" || c.type === "bulb");
  const bulbs = components.filter(c => c.type === "bulb");
  const branchCurrents = wires.map((_, index) => {
    const exact = solution.wire_currents?.[index];
    if (exact?.resolved) return { exact: exact.current, magnitude: Math.abs(exact.current) };
    return { exact: null, magnitude: 0 };
  });
  const branchColors = ["#527a95", "#a98a4f", "#a8674c", "#647d68", "#806d87", "#9a6658"];
  const branchColorById = new Map(resistors.map((component, index) => [component.id, branchColors[index % branchColors.length]]));
  const colorForWire = (wire, index) => {
    const branchId = [wire.from_component, wire.to_component].find((id) => branchColorById.has(id));
    return branchId ? branchColorById.get(branchId) : branchColors[index % branchColors.length];
  };
  const dashFlow = (value) => {
    // Solved amperes drive this visual cue; it is not a literal drift-speed model.
    const amperes = Math.max(0, Number(value) || 0);
    const fraction = Math.min(1, Math.log1p(amperes / 0.05) / Math.log1p(20));
    const dashLength = 3 + fraction * 3;
    const gapLength = 20 - fraction * 9;
    return { dashArray: `${dashLength} ${gapLength}`, dashOffset: -(dashLength + gapLength),
      strokeWidth: 2.5 + fraction * 1.8, duration: 1.8 - fraction * 1.25 };
  };

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
          maxWidth: "100%",
          border: "1px solid #deddd7",
          borderRadius: 8,
          background: "#fffefa"
        }}
      >
        <defs>
          <filter id="generatedBulbGlow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="10" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        {/* AI Wire Paths */}
        {wires.map((wire, index) => {
          const flow = branchCurrents[index] || { exact: null, magnitude: 0 };
          const color = flow.exact === null ? "#94a3b8" : colorForWire(wire, index);
          const flowStyle = dashFlow(flow.magnitude);
          const pathPoints = flow.exact < 0 ? [...wire.points].reverse() : wire.points;
          return <g key={index}>
            <path d={makePath(wire.points)} fill="none" stroke={color} strokeWidth={flow.exact === null ? 3 : flowStyle.strokeWidth + 3}
              strokeLinecap="round" strokeLinejoin="round" opacity={flow.exact === null ? 0.24 : 0.22} />
            {flow.exact !== null && flow.magnitude > 0 && <>
              <path d={makePath(pathPoints)} fill="none" stroke={color} strokeWidth={flowStyle.strokeWidth} strokeLinecap="round"
                strokeDasharray={flowStyle.dashArray} opacity=".98">
                <animate attributeName="stroke-dashoffset" from="0" to={flowStyle.dashOffset}
                  dur={`${flowStyle.duration}s`} repeatCount="indefinite" />
              </path>
            </>}
          </g>;
        })}

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
              {r.type === "bulb" ? <>
                <circle cx={cx} cy={cy} r={Math.max(x2 - x1, y2 - y1) * 0.65} fill="#facc15" opacity={Number(result?.power) > 1e-12 ? 0.12 + Math.min(1, Math.log1p(Math.max(0, Number(result?.power) || 0)) / Math.log1p(5)) * 0.38 : 0} filter="url(#generatedBulbGlow)" />
                <circle cx={cx} cy={cy} r={Math.max(10, Math.min(x2 - x1, y2 - y1) / 2)} fill={Number(result?.power) > 1e-12 ? "#fff7ae" : "#d3d3ce"} stroke="#9b8b62" strokeWidth="3" />
              </> : <rect x={x1} y={y1} width={x2 - x1} height={y2 - y1} rx="4" fill="white" stroke="#1e293b" strokeWidth="2" />}

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

      <div style={{ marginTop: 25 }}>
        <h3>Bulbs detected ({bulbs.length})</h3>
        {bulbs.length ? bulbs.map((bulb) => {
          const result = solution.components?.[bulb.id] || {};
          return <p key={bulb.id}>💡 <strong>{bulb.id}</strong> — {bulb.value ?? "Unknown"} Ω · {Number(result.current || 0).toFixed(3)} A · {Number(result.power || 0).toFixed(2)} W</p>;
        }) : <p>No bulbs were identified in this circuit.</p>}
      </div>
    </div>
  );
}

export default GeneratedCircuitAI;
