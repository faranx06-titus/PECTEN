import { useEffect, useRef, useState } from "react";
import { simulateCircuit } from "../services/api";
import TopologyEditor from "./TopologyEditor";
import { assignTerminalToNode, getCircuitNodes, normalizeCircuitNodes } from "../utils/circuitTopology";

const CURRENT_COLORS = ["#527a95", "#a8674c", "#c7a653"];
const BRANCH_COLORS = ["#527a95", "#a98a4f", "#a8674c", "#647d68", "#806d87", "#9a6658"];

function mixColors(start, end, amount) {
  const channel = (hex, offset) => parseInt(hex.slice(offset, offset + 2), 16);
  const t = Math.min(1, Math.max(0, amount));
  return `#${[1, 3, 5].map((offset) => Math.round(channel(start, offset) * (1 - t) + channel(end, offset) * t)
    .toString(16).padStart(2, "0")).join("")}`;
}

function AnalyzedCircuitSimulator({ analysis, imageUrl, onSimulationChange, topologyReviewed, onTopologyReviewedChange }) {
  const [editedData, setEditedData] = useState(() => {
    const vision = analysis?.vision;
    return vision?.circuit ? { ...vision, circuit: normalizeCircuitNodes(vision.circuit) } : vision;
  });
  const [simulation, setSimulation] = useState(analysis?.solution ?? null);
  const [selectedTerminal, setSelectedTerminal] = useState(null);
  const [topologyEditing, setTopologyEditing] = useState(false);
  const [resolvedReviewIds, setResolvedReviewIds] = useState([]);
  const [error, setError] = useState("");
  const [simulationPending, setSimulationPending] = useState(false);
  const [sourceDimensions, setSourceDimensions] = useState(null);
  const [sourceImageError, setSourceImageError] = useState(false);
  const requestId = useRef(0);
  const initialEffectSkipped = useRef(false);
  const circuit = editedData?.circuit;
  const visual = editedData?.visual ?? {};

  useEffect(() => {
    if (!editedData?.circuit) return undefined;
    // /analyze-circuit already solved this exact initial graph. Reuse that
    // result instead of flashing an empty preview and immediately solving it
    // a second time; subsequent edits still go through /simulate-circuit.
    if (!initialEffectSkipped.current && (analysis?.solution || analysis?.simulation_error)) {
      initialEffectSkipped.current = true;
      return undefined;
    }
    initialEffectSkipped.current = true;
    const id = ++requestId.current;
    setSimulationPending(true);
    simulateCircuit(editedData)
      .then((result) => {
        if (requestId.current !== id) return;
        setSimulation(result);
        setError("");
        onSimulationChange?.(result);
      })
      .catch((reason) => {
        if (requestId.current === id) setError(reason.message);
      })
      .finally(() => {
        if (requestId.current === id) setSimulationPending(false);
      });
    return () => { requestId.current += 1; };
  }, [editedData, onSimulationChange]);

  if (!circuit || !imageUrl) return null;

  const changeValue = (componentId, value) => {
    setSimulation(null);
    setEditedData((current) => ({
      ...current,
      circuit: {
        ...current.circuit,
        components: current.circuit.components.map((component) =>
          component.id === componentId ? { ...component, value: Number(value) } : component),
      },
    }));
  };

  const changeTopology = (nextCircuit) => {
    const previousNodes = getCircuitNodes(circuit);
    const nextNodes = getCircuitNodes(nextCircuit);
    const sameNode = (nodes, first, second) => nodes.some((node) =>
      node.terminals.some((endpoint) => endpoint.component === first.component && endpoint.terminal === first.terminal)
      && node.terminals.some((endpoint) => endpoint.component === second.component && endpoint.terminal === second.terminal));
    const answeredByEdit = reviewItems.filter((item) => {
      const endpoints = item.endpoints;
      return item.kind !== "component" && Array.isArray(endpoints) && endpoints.length === 2
        && sameNode(previousNodes, endpoints[0], endpoints[1]) !== sameNode(nextNodes, endpoints[0], endpoints[1]);
    }).map((item) => item.id).filter(Boolean);
    if (answeredByEdit.length) {
      setResolvedReviewIds((current) => [...new Set([...current, ...answeredByEdit])]);
    }
    onTopologyReviewedChange(false);
    setSelectedTerminal(null);
    setSimulation(null);
    setEditedData((current) => ({ ...current, circuit: nextCircuit }));
  };

  const selectTopologyTerminal = (endpoint) => {
    if (!selectedTerminal) {
      setSelectedTerminal(endpoint);
      return;
    }
    if (selectedTerminal.component === endpoint.component && selectedTerminal.terminal === endpoint.terminal) {
      setSelectedTerminal(null);
      return;
    }

    const sourceNode = topologyNodes.find((node) => node.terminals.some((item) =>
      item.component === selectedTerminal.component && item.terminal === selectedTerminal.terminal));
    const targetNode = topologyNodes.find((node) => node.terminals.some((item) =>
      item.component === endpoint.component && item.terminal === endpoint.terminal));
    if (sourceNode && targetNode && sourceNode.id !== targetNode.id) {
      const nodes = topologyNodes
        .filter((node) => node.id !== targetNode.id)
        .map((node) => node.id === sourceNode.id
          ? { ...node, terminals: [...node.terminals, ...targetNode.terminals] }
          : node);
      changeTopology(normalizeCircuitNodes({ ...circuit, nodes }));
      return;
    }
    setSelectedTerminal(null);
  };

  const separateSelectedTerminal = () => {
    if (!selectedTerminal) return;
    changeTopology(assignTerminalToNode(
      circuit,
      selectedTerminal.component,
      selectedTerminal.terminal,
      "__new__",
    ));
  };

  const answerTopologyReview = (item, connected) => {
    if (connected === null) return;
    const endpoints = (Array.isArray(item.endpoints) ? item.endpoints : [])
      .filter((endpoint) => endpoint?.component && endpoint?.terminal);
    if (endpoints.length === 2) {
      const [first, second] = endpoints;
      const nodes = getCircuitNodes(circuit);
      const firstNode = nodes.find((node) => node.terminals.some((endpoint) =>
        endpoint.component === first.component && endpoint.terminal === first.terminal));
      const secondNode = nodes.find((node) => node.terminals.some((endpoint) =>
        endpoint.component === second.component && endpoint.terminal === second.terminal));
      if (firstNode && secondNode && connected && firstNode.id !== secondNode.id) {
        const merged = nodes.filter((node) => node.id !== secondNode.id).map((node) =>
          node.id === firstNode.id ? { ...node, terminals: [...node.terminals, ...secondNode.terminals] } : node);
        changeTopology(normalizeCircuitNodes({ ...circuit, nodes: merged }));
      } else if (firstNode && secondNode && !connected && firstNode.id === secondNode.id) {
        changeTopology(assignTerminalToNode(circuit, second.component, second.terminal, "__new__"));
      }
    }
    const reviewId = item.id;
    setResolvedReviewIds((current) => current.includes(reviewId) ? current : [...current, reviewId]);
  };

  const answerComponentReview = (item, componentType) => {
    const nextCircuit = {
      ...circuit,
      components: circuit.components.map((component) =>
        component.id === item.component ? { ...component, type: componentType } : component),
    };
    changeTopology(nextCircuit);
    setResolvedReviewIds((current) => current.includes(item.id) ? current : [...current, item.id]);
  };

  const components = circuit.components ?? [];
  const topologyNodes = getCircuitNodes(circuit);
  const reviewItems = Array.isArray(editedData?.review_items)
    ? editedData.review_items.filter((item) => item && typeof item === "object")
    : [];
  const pendingReviewEndpointKeys = new Set(reviewItems
    .filter((item, index) => !resolvedReviewIds.includes(item.id ?? `review-${index + 1}`))
    .flatMap((item) => Array.isArray(item.endpoints) ? item.endpoints : [])
    .filter((endpoint) => endpoint?.component && endpoint?.terminal)
    .map((endpoint) => `${endpoint.component}::${endpoint.terminal}`));
  const pendingReviewComponentIds = new Set(reviewItems
    .filter((item, index) => !resolvedReviewIds.includes(item.id ?? `review-${index + 1}`))
    .filter((item) => item.kind === "component" || item.component)
    .map((item) => item.component)
    .filter(Boolean));
  const nodeColors = new Map();
  const topologyPalette = ["#54758a", "#92724e", "#647d68", "#806d87", "#9a6658"];
  topologyNodes.forEach((node, index) => nodeColors.set(node.id, topologyPalette[index % topologyPalette.length]));
  const nodeForTerminal = new Map();
  topologyNodes.forEach((node) => node.terminals.forEach((endpoint) =>
    nodeForTerminal.set(`${endpoint.component}::${endpoint.terminal}`, node.id)));
  const results = simulation?.components ?? {};
  const physicsPassed = !simulationPending && (simulation?.physics_checks?.passed ?? simulation?.kcl_check?.passed ?? false)
    && (simulation?.topology_check?.passed ?? true);
  const topologyWarnings = simulation?.topology_check?.warnings ?? [];
  const actionableReviewItems = reviewItems.filter((item, index) => {
    const id = item.id ?? `review-${index + 1}`;
    const hasTarget = (Array.isArray(item.endpoints) && item.endpoints.length === 2)
      || item.kind === "component" || Boolean(item.component);
    return hasTarget && !resolvedReviewIds.includes(id);
  });
  const canStartSimulation = Boolean(simulation) && physicsPassed && actionableReviewItems.length === 0 && !error && !simulationPending;
  const wires = visual.wire_paths ?? [];
  const width = visual.image_width || 700;
  const height = visual.image_height || 400;
  const bulbs = components.filter((component) => component.type === "bulb");
  const wireCurrents = wires.map((_, index) => {
    if (!topologyReviewed || !physicsPassed) return { exact: null, magnitude: 0 };
    const solved = simulation?.wire_currents?.[index];
    return solved?.resolved
      ? { exact: Number(solved.current), magnitude: Math.abs(Number(solved.current)) }
      : { exact: null, magnitude: 0 };
  });
  const solvedBranches = components
    .filter((component) => ["resistor", "bulb"].includes(component.type))
    .map((component) => ({ component, result: results[component.id] }))
    .filter(({ result }) => topologyReviewed && physicsPassed && result && Number.isFinite(Number(result.current)));
  const resolvedWireCount = wireCurrents.filter((flow) => flow.exact !== null && flow.magnitude > 0).length;
  const activeBranchCount = solvedBranches.filter(({ result }) => Math.abs(Number(result.current)) > 1e-12).length;
  const branchCurrentMagnitudes = solvedBranches.map(({ result }) => Math.abs(Number(result.current))).filter((value) => value > 1e-12);
  const highestBranchCurrent = Math.max(...branchCurrentMagnitudes);
  const branchColorById = new Map(solvedBranches.map(({ component }, index) =>
    [component.id, BRANCH_COLORS[index % BRANCH_COLORS.length]]));
  const animatedBranchCount = solvedBranches.filter(({ component }) => {
    const terminals = component.visual?.terminal_points ?? {};
    const first = terminals[component.terminals?.[0] ?? "1"];
    const second = terminals[component.terminals?.[1] ?? "2"];
    return [first, second].every((point) => Array.isArray(point) && point.length === 2 && point.every(Number.isFinite));
  }).filter(({ result }) => Math.abs(Number(result.current)) > 1e-12).length;
  const flowStatus = !topologyReviewed
    ? "Start the simulation to animate solved current."
    : wires.length === 0
      ? "No wire paths were detected in this image, so there is no path to animate."
      : resolvedWireCount === 0
        ? "The circuit values are solved, but the detected wire paths could not be matched to current directions."
        : `Current animation is active on ${resolvedWireCount} of ${wires.length} detected wire paths.`;
  const wireColor = (current, branchId) => {
    if (branchId && branchColorById.has(branchId)) return branchColorById.get(branchId);
    const range = highestBranchCurrent - lowestBranchCurrent;
    const amount = range <= 1e-12 ? 0.5 : (current - lowestBranchCurrent) / range;
    return amount <= 0.5
      ? mixColors(CURRENT_COLORS[0], CURRENT_COLORS[1], amount * 2)
      : mixColors(CURRENT_COLORS[1], CURRENT_COLORS[2], (amount - 0.5) * 2);
  };
  const dashFlow = (current) => {
    // This is a visual current cue, not electron drift speed. Use absolute
    // solved amperes so changing the source voltage or any resistance changes
    // the animation even when every branch scales by the same factor.
    const amperes = Math.max(0, Number(current) || 0);
    const fraction = Math.min(1, Math.log1p(amperes / 0.05) / Math.log1p(20));
    const dashLength = 3 + fraction * 3;
    const gapLength = 20 - fraction * 9;
    return {
      dashArray: `${dashLength} ${gapLength}`,
      dashOffset: -(dashLength + gapLength),
      strokeWidth: 2.5 + fraction * 1.8,
      duration: 1.8 - fraction * 1.25,
    };
  };
  const questionText = analysis?.vision?.problem?.text ?? "";
  const requestedText = `${analysis?.vision?.problem?.asked_quantity ?? ""} ${questionText}`.toLowerCase();
  const requestedQuantity = /power|watt|dissipat/.test(requestedText) ? "power"
    : /brightness|bright|glow/.test(requestedText) ? "brightness"
      : /voltage|potential difference|potential drop/.test(requestedText) ? "voltage"
        : /resistance|equivalent resistance/.test(requestedText) ? "resistance"
          : /current|ampere|amperage/.test(requestedText) ? "current" : null;
  const requestedLabel = questionText.match(/\b([A-Z])[_ ]?(\d+)\b/i);
  const requestedComponentId = requestedLabel ? `${requestedLabel[1]}${requestedLabel[2]}`.toUpperCase() : null;
  const requestedComponent = components.find((component) => component.id.toUpperCase() === requestedComponentId);
  const batteryComponents = components.filter((component) => ["battery", "cell"].includes(component.type));
  const sourceResults = simulation?.sources ?? batteryComponents.map((source) => ({ id: source.id, ...results[source.id],
    supplied_current: -Number(results[source.id]?.current ?? 0), supplied_power: -Number(results[source.id]?.power ?? 0) }));
  const sourceGroups = [...sourceResults.reduce((groups, source, index) => {
    const key = source.group_id ?? `source-${index}`;
    groups.set(key, [...(groups.get(key) ?? []), source]);
    return groups;
  }, new Map()).entries()];
  let requestedAnswer = null;
  if (requestedQuantity === "brightness" || (requestedQuantity === "power" && (requestedComponent?.type === "bulb" || (!requestedComponent && /bulb|lamp/.test(questionText.toLowerCase()))))) {
    const selectedBulbs = requestedComponent?.type === "bulb" ? [requestedComponent] : bulbs;
    if (selectedBulbs.length) requestedAnswer = `${selectedBulbs.map((bulb) => `${bulb.id}: ${Number(results[bulb.id]?.power ?? 0).toFixed(3)} W`).join(" · ")}${requestedQuantity === "brightness" ? " electrical power; relative glow follows power" : ""}`;
  } else if (requestedQuantity === "power") {
    const source = requestedComponent && sourceResults.find((item) => item.id === requestedComponent.id);
    const sourceQuestion = !requestedComponent && /battery|cell|source/.test(questionText.toLowerCase());
    const power = source ? Number(source.supplied_power) : requestedComponent
      ? Number(results[requestedComponent.id]?.power) : components
        .filter((component) => ["resistor", "bulb"].includes(component.type))
        .reduce((sum, component) => sum + Number(results[component.id]?.power ?? 0), 0);
    if (sourceQuestion && sourceResults.length) requestedAnswer = sourceGroups.map(([, group]) => `${group.map((item) => item.id).join(" + ")}: ${group.reduce((sum, item) => sum + Number(item.supplied_power ?? -item.power), 0).toFixed(3)} W supplied`).join(" · ");
    else if (Number.isFinite(power)) requestedAnswer = `${Math.abs(power).toFixed(3)} W`;
  } else if (requestedQuantity === "voltage") {
    if (requestedComponent && results[requestedComponent.id]) requestedAnswer = `${Math.abs(Number(results[requestedComponent.id].voltage)).toFixed(3)} V across ${requestedComponent.id}`;
    else if (sourceResults.length === 1) requestedAnswer = `${Math.abs(Number(sourceResults[0].voltage)).toFixed(3)} V across ${sourceResults[0].id}`;
    else if (sourceResults.length > 1) requestedAnswer = sourceResults.map((source) => `${source.id}: ${Math.abs(Number(source.voltage)).toFixed(3)} V`).join(" · ");
  } else if (requestedQuantity === "resistance") {
    if (requestedComponent && requestedComponent.value != null) requestedAnswer = `${Number(requestedComponent.value).toFixed(3)} Ω for ${requestedComponent.id}`;
    else if (simulation?.equivalent_resistance != null && Number.isFinite(Number(simulation.equivalent_resistance))) requestedAnswer = `${Number(simulation.equivalent_resistance).toFixed(3)} Ω`;
    else requestedAnswer = "A single equivalent resistance is not defined for this multi-source network.";
  } else if (requestedQuantity === "current") {
    const source = requestedComponent && sourceResults.find((item) => item.id === requestedComponent.id);
    if (source) requestedAnswer = `${Number(source.supplied_current).toFixed(3)} A supplied by ${source.id} (signed; negative means charging)`;
    else if (requestedComponent && results[requestedComponent.id]) requestedAnswer = `${Math.abs(Number(results[requestedComponent.id].current)).toFixed(3)} A through ${requestedComponent.id}`;
    else if (sourceResults.length === 1) requestedAnswer = `${Math.abs(Number(simulation?.total_current ?? 0)).toFixed(3)} A supplied by ${sourceResults[0].id}`;
    else if (sourceResults.length > 1) requestedAnswer = sourceGroups.map(([, group]) => {
      const groupCurrent = group[0].group_supplied_current ?? group.reduce((sum, source) => sum + Number(source.supplied_current ?? -source.current), 0);
      const equalShare = group.length > 1
        ? ` (${group.map((source) => `${source.id}: ${Number(source.supplied_current ?? -source.current).toFixed(3)} A equal-share estimate`).join(", ")})`
        : "";
      return `${group.map((source) => source.id).join(" + ")}: ${Number(groupCurrent).toFixed(3)} A supplied${equalShare}`;
    }).join(" · ");
  }

  return (
    <div className="analyzed-simulation">
      <div className="simulation-heading">
        <div>
          <p className="simulation-eyebrow">PECTEN · LIVE CIRCUIT MODEL</p>
          <h2>Interactive Circuit Simulation</h2>
          <p>Change a component value to explore the result. Check any highlighted connection before starting the current animation.</p>
        </div>
        {simulation && <div className={topologyReviewed ? "live-badge" : "candidate-badge"}><span /> {topologyReviewed ? "CONNECTIONS CHECKED" : "PREVIEW"}</div>}
      </div>

      <TopologyEditor
        circuit={circuit}
        nodeColors={nodeColors}
        selectedTerminal={selectedTerminal}
        onTerminalSelect={selectTopologyTerminal}
        onReviewEndpointSelect={setSelectedTerminal}
        onSeparateTerminal={separateSelectedTerminal}
        reviewItems={reviewItems}
        resolvedReviewIds={resolvedReviewIds}
        onReviewAnswer={answerTopologyReview}
        onReviewComponentType={answerComponentReview}
        onAdvancedChange={setTopologyEditing}
      />
      <div className={`topology-confirmation${topologyReviewed ? " is-confirmed" : ""}`}>
        <span>{simulationPending ? "Recalculating the circuit…" : !physicsPassed ? "The circuit failed a physics check, so current flow is paused." : actionableReviewItems.length ? `Answer or correct ${actionableReviewItems.length} unclear circuit item${actionableReviewItems.length === 1 ? "" : "s"} before starting.` : topologyReviewed ? "Simulation running for this diagram." : "Check the picture and the detected connections, then start."}</span>
        <button type="button" disabled={!canStartSimulation} onClick={() => onTopologyReviewedChange(true)}>
          {topologyReviewed ? "Simulation started" : "Looks right — start current flow"}
        </button>
      </div>

      <details className="readable-node-check">
        <summary>Show the connections PECTEN read</summary>
        <p>Each row lists component ends that PECTEN believes share one continuous wire connection.</p>
        {topologyWarnings.length > 0 && <div className="topology-diagnostic" role="status">
          <strong>Check these possible connection problems</strong>
          <ul>{topologyWarnings.map((warning, index) => <li key={`${warning.kind}-${index}`}>{warning.message}</li>)}</ul>
        </div>}
        <ul>{topologyNodes.map((node) => <li key={`read-${node.id}`}>
          <strong>{node.terminals.length > 1 ? "Connected ends" : "Unconnected end"}</strong>
          <span>{node.terminals.map((endpoint) => `${endpoint.component}, end ${endpoint.terminal}`).join(" · ")}</span>
        </li>)}</ul>
      </details>

      <div className="simulation-metrics">
        <div><span>{sourceResults.length > 1 ? "Battery and cell sources" : "Source voltage"}</span><strong>{sourceResults.length > 1 ? sourceResults.length : `${Math.abs(Number(simulation?.voltage ?? 0)).toFixed(2)} V`}</strong></div>
        <div><span>Equivalent resistance</span><strong>{simulation?.equivalent_resistance != null && Number.isFinite(Number(simulation.equivalent_resistance)) ? `${Number(simulation.equivalent_resistance).toFixed(2)} Ω` : "—"}</strong></div>
        <div><span>{sourceResults.length > 1 ? `${simulation?.primary_source_id ?? sourceResults[0]?.id ?? "Source"} group current` : "Total current"}</span><strong className="current-metric">{Number(simulation?.total_current ?? 0).toFixed(2)} <small>A</small></strong></div>
      </div>
      {requestedAnswer && <section className="requested-answer" aria-live="polite">
        <span>Answer{questionText ? ` · ${questionText}` : " to the requested quantity"}</span>
        <strong>{requestedAnswer}</strong>
      </section>}

      <div className="simulation-workspace">
        <section className="diagram-card">
          <div className="diagram-card-heading">
            <h3>Current map</h3>
            <span>{physicsPassed ? "Kirchhoff and component checks passed" : "Physics checks failed; animation is paused"}</span>
          </div>
          <p className={`flow-status${topologyReviewed && activeBranchCount === 0 ? " is-unavailable" : ""}`} role="status">
            {topologyReviewed && physicsPassed
              ? `Physics found nonzero current in ${activeBranchCount} of ${solvedBranches.length} resistor and bulb branches; ${animatedBranchCount} have image coordinates for animation. ${resolvedWireCount} wire paths have a KCL-consistent direction for animation.`
              : !physicsPassed ? "PECTEN will not animate results that fail its current, voltage, or power checks. Correct the circuit and solve again." : flowStatus}
          </p>
          <p className="physics-note">Changing a source voltage or component resistance recalculates node voltage, branch current, and power. Dash pace and thickness visualize solved current; bulb glow responds to solved power. Dash motion is a visual cue, not literal electron drift speed.</p>
          <div className="source-image-frame">
            <img src={imageUrl} alt="Uploaded circuit diagram" onError={() => setSourceImageError(true)} onLoad={(event) => {
              setSourceImageError(false);
              setSourceDimensions({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight });
            }} />
            {visual.image_width && visual.image_height && <svg viewBox={`0 0 ${sourceDimensions?.width || width} ${sourceDimensions?.height || height}`}
              preserveAspectRatio="none" aria-label="Animated current and bulb brightness overlay">
              <defs>
                <filter id="pectenBulbGlow" x="-150%" y="-150%" width="400%" height="400%">
                  <feGaussianBlur stdDeviation="12" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              </defs>
              {components.filter((component) => pendingReviewComponentIds.has(component.id)).map((component) => {
                const box = component.visual?.bbox;
                if (!Array.isArray(box) || box.length !== 4) return null;
                return <g key={`review-${component.id}`} pointerEvents="none">
                  <rect x={box[0] - 6} y={box[1] - 6} width={box[2] - box[0] + 12} height={box[3] - box[1] + 12}
                    rx="7" fill="rgba(245,158,11,.12)" stroke="#f59e0b" strokeWidth="4" strokeDasharray="8 5" />
                  <text x={box[0]} y={box[1] - 10} fill="#92400e" stroke="#fff7ed" strokeWidth="4" paintOrder="stroke" fontSize="15" fontWeight="700">Check {component.id}</text>
                </g>;
              })}
              {wires.map((wire, index) => {
                const wirePoints = wire.points ?? [];
                if (wirePoints.length < 2) return null;
                const points = wirePoints.map(([x, y]) => `${x},${y}`).join(" ");
                const path = wirePoints.map(([x, y], pointIndex) => `${pointIndex ? "L" : "M"} ${x} ${y}`).join(" ");
                const flow = wireCurrents[index] ?? { exact: null, magnitude: 0 };
                const branchCurrent = flow.magnitude;
                const branchOwner = [wire.from_component, wire.to_component].find((componentId) => branchColorById.has(componentId));
                const color = flow.exact === null ? "#94a3b8" : wireColor(branchCurrent, branchOwner);
                const animationPath = flow.exact < 0
                  ? [...wirePoints].reverse().map(([x, y], pointIndex) => `${pointIndex ? "L" : "M"} ${x} ${y}`).join(" ")
                  : path;
                const flowStyle = dashFlow(branchCurrent);
                return <g key={`${wire.from_component}-${wire.to_component}-${index}`} pointerEvents="none">
                  <polyline points={points} fill="none" stroke={color} strokeWidth={flow.exact === null ? 3 : flowStyle.strokeWidth + 3}
                    strokeLinecap="round" strokeLinejoin="round" opacity={flow.exact === null ? 0.24 : 0.22} />
                  {flow.exact !== null && branchCurrent > 0 && <>
                    <path d={animationPath} fill="none" stroke={color} strokeWidth={flowStyle.strokeWidth} strokeLinecap="round"
                      strokeDasharray={flowStyle.dashArray} opacity=".98">
                      <animate attributeName="stroke-dashoffset" from="0" to={flowStyle.dashOffset}
                        dur={`${flowStyle.duration}s`} repeatCount="indefinite" />
                    </path>
                  </>}
                </g>;
              })}
              {solvedBranches.map(({ component, result }) => {
                const terminalPoints = component.visual?.terminal_points ?? {};
                const first = terminalPoints[component.terminals?.[0] ?? "1"];
                const second = terminalPoints[component.terminals?.[1] ?? "2"];
                if (![first, second].every((point) => Array.isArray(point) && point.length === 2 && point.every(Number.isFinite))) return null;
                const current = Number(result.current);
                const magnitude = Math.abs(current);
                if (magnitude <= 1e-12) return null;
                const start = current < 0 ? second : first;
                const end = current < 0 ? first : second;
                const path = `M ${start[0]} ${start[1]} L ${end[0]} ${end[1]}`;
                const color = wireColor(magnitude, component.id);
                const flowStyle = dashFlow(magnitude);
                return <g key={`branch-flow-${component.id}`} pointerEvents="none" aria-label={`${component.id} current ${magnitude.toFixed(3)} amperes`}>
                  <path d={path} fill="none" stroke={color} strokeWidth={flowStyle.strokeWidth + 3} strokeLinecap="round" opacity=".22" />
                  <path d={path} fill="none" stroke={color} strokeWidth={flowStyle.strokeWidth} strokeLinecap="round"
                    strokeDasharray={flowStyle.dashArray} opacity=".98">
                    <animate attributeName="stroke-dashoffset" from="0" to={flowStyle.dashOffset}
                      dur={`${flowStyle.duration}s`} repeatCount="indefinite" />
                  </path>
                </g>;
              })}
              {components.flatMap((component) => (component.terminals ?? []).map((terminal) => {
                const point = component.visual?.terminal_points?.[terminal];
                const nodeId = nodeForTerminal.get(`${component.id}::${terminal}`);
                if (!Array.isArray(point) || point.length !== 2 || !nodeId) return null;
                const selected = component.id === selectedTerminal?.component && terminal === selectedTerminal?.terminal;
                const needsReview = pendingReviewEndpointKeys.has(`${component.id}::${terminal}`);
                const choose = (event) => {
                  event.stopPropagation();
                  selectTopologyTerminal({ component: component.id, terminal });
                };
                return <g key={`node-${component.id}-${terminal}`} role={topologyEditing ? "button" : undefined} tabIndex={topologyEditing ? 0 : undefined}
                  aria-label={`${component.id} terminal ${terminal}, node ${nodeId}`}
                  onClick={topologyEditing ? choose : undefined}
                  onKeyDown={topologyEditing ? (event) => { if (event.key === "Enter" || event.key === " ") choose(event); } : undefined}
                  style={topologyEditing ? { cursor: "pointer", pointerEvents: "auto" } : { pointerEvents: "none" }}>
                  {topologyEditing && <>
                    <circle cx={point[0]} cy={point[1]} r="13" fill={nodeColors.get(nodeId)} stroke="#fff" strokeWidth="2" opacity=".94" />
                    <text x={point[0]} y={point[1] + 4} textAnchor="middle" fontSize="10" fontWeight="700" fill="#fff">{nodeId}</text>
                  </>}
                  {needsReview && <circle cx={point[0]} cy={point[1]} r="19" fill="none" stroke="#f59e0b" strokeWidth="3" strokeDasharray="4 3" />}
                  {selected && <circle cx={point[0]} cy={point[1]} r="18" fill="none" stroke="#facc15" strokeWidth="3" />}
                </g>;
              }))}
              {topologyReviewed && physicsPassed && bulbs.map((bulb) => {
                const box = bulb.visual?.bbox;
                const center = bulb.visual?.center ?? (box ? [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2] : null);
                if (!center) return null;
                const power = Math.max(0, Number(results[bulb.id]?.power) || 0);
                const relativePower = Math.min(1, Math.log1p(power) / Math.log1p(5));
                const radius = box ? Math.max(box[2] - box[0], box[3] - box[1]) * 0.72 : 24;
                return <g key={`glow-${bulb.id}`} pointerEvents="none">
                  <circle cx={center[0]} cy={center[1]} r={radius} fill="#facc15" opacity={power > 1e-12 ? 0.12 + relativePower * 0.42 : 0} filter="url(#pectenBulbGlow)" />
                  <circle cx={center[0]} cy={center[1]} r={Math.max(5, radius * 0.24)} fill={power > 1e-12 ? "#fff7ae" : "#b8b8b2"} opacity={power > 1e-12 ? 0.3 + relativePower * 0.65 : 0.45} />
                </g>;
              })}
            </svg>}
          </div>
          {sourceImageError && <p className="image-error-message" role="alert">The circuit was analyzed, but this browser could not display the cropped image. Return to the upload page and choose the crop again.</p>}
          <div className="current-legend">
            {branchCurrentMagnitudes.length === 0 ? <span>Each branch gets its own color after the simulation starts.</span>
              : <>
                {solvedBranches.filter(({ result }) => Math.abs(Number(result.current)) > 1e-12).map(({ component, result }) => <span key={`legend-${component.id}`}>
                  <i style={{ background: branchColorById.get(component.id) }} />{component.id}: {Math.abs(Number(result.current)).toFixed(3)} A
                </span>)}
                <span className="current-legend-note">Dash thickness and spacing show relative current.</span>
              </>}
          </div>
        </section>

        <section className="component-editor">
          <h3>Adjust components</h3>
          <p>Edits recalculate the circuit immediately.</p>
          {components.map((component) => {
            const isBattery = ["battery", "cell"].includes(component.type);
            const editable = isBattery || ["resistor", "bulb"].includes(component.type);
            const result = physicsPassed ? results[component.id] : null;
            return <label className="component-control" key={component.id}>
              <span className="component-control-title"><b>{component.id}</b><small>{component.type}</small></span>
              <span className="component-input-wrap">
                {editable ? <input aria-label={`${component.id} value`} type="number" min="0.01" step="any" value={component.value ?? ""}
                  onChange={(event) => changeValue(component.id, event.target.value)} /> : <span>{component.value ?? "unknown"}</span>}
                <small>{isBattery ? "V" : "Ω"}</small>
              </span>
              {result && ["resistor", "bulb"].includes(component.type) && (() => {
                const terminals = component.terminals ?? ["1", "2"];
                const forward = Number(result.current) >= 0;
                const direction = forward ? `${terminals[0]} → ${terminals[1]}` : `${terminals[1]} → ${terminals[0]}`;
                return <small className="component-current">{Math.abs(Number(result.current) || 0).toFixed(3)} A · {direction} · {Math.abs(Number(result.voltage) || 0).toFixed(2)} V · {Number(result.power || 0).toFixed(2)} W</small>;
              })()}
              {result && isBattery && <small className="component-current">{Math.abs(Number(result.current) || 0).toFixed(3)} A · {Number(result.power || 0) <= 0 ? "supplying" : "charging"} · {Math.abs(Number(result.power) || 0).toFixed(2)} W{sourceResults.find((source) => source.id === component.id)?.sharing_assumption === "equal" ? " · equal-share estimate" : ""}</small>}
            </label>;
          })}
          {error && <p className="simulation-error" role="alert">Simulation unavailable: {error}</p>}
        </section>
      </div>

      <section className="bulb-results">
        <div className="diagram-card-heading"><div><p className="simulation-eyebrow">LIGHT OUTPUT</p><h3>Bulb response ({bulbs.length})</h3><span>Electrical power is solved from the circuit; glow is a qualitative visual indicator because bulb ratings are unknown.</span></div></div>
        {bulbs.length === 0 ? <p>No bulbs were identified in this diagram.</p> : <div className="bulb-list">
          {bulbs.map((bulb) => {
            const result = physicsPassed ? results[bulb.id] : null;
            const power = Math.max(0, Number(result?.power) || 0);
            const intensity = Math.min(1, Math.log1p(power) / Math.log1p(5));
            return <article className="bulb-card" key={bulb.id}>
              <span className="bulb-indicator" style={{ opacity: power > 1e-12 ? 0.3 + intensity * 0.7 : 0.22, boxShadow: power > 1e-12 ? `0 0 ${8 + intensity * 26}px ${CURRENT_COLORS[2]}` : "none" }}>✦</span>
              <div><strong>{bulb.id}</strong><small>{bulb.value ?? "Unknown"} Ω</small></div>
              <div className="bulb-stats"><span>{Math.abs(Number(result?.current) || 0).toFixed(3)} A</span><span>{Number(result?.voltage || 0).toFixed(2)} V</span><b>{power.toFixed(2)} W</b></div>
              <div className="brightness-track"><i style={{ width: `${intensity * 100}%` }} /></div>
            </article>;
          })}
        </div>}
      </section>
    </div>
  );
}

export default AnalyzedCircuitSimulator;
