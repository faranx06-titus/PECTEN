import { useState } from "react";
import { getCircuitNodes } from "../utils/circuitTopology";

function TopologyEditor({ circuit, nodeColors, selectedTerminal, onTerminalSelect, onReviewEndpointSelect, onSeparateTerminal, onReviewAnswer, onReviewComponentType, onAdvancedChange, reviewItems = [], resolvedReviewIds = [] }) {
  const [expanded, setExpanded] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const identifiedReviews = reviewItems.map((item, index) => ({ ...item, id: item.id ?? `review-${index + 1}` }));
  const pendingReviews = identifiedReviews.filter((item) => !resolvedReviewIds.includes(item.id));
  const nodes = getCircuitNodes(circuit);
  const selectedNode = selectedTerminal
    ? nodes.find((node) => node.terminals.some((endpoint) =>
      endpoint.component === selectedTerminal.component && endpoint.terminal === selectedTerminal.terminal))
    : null;

  return (
    <section className={`topology-review${expanded ? " is-expanded" : ""}`}>
      <div className="topology-review-heading">
        <div>
          <h3>Check the circuit{pendingReviews.length > 0 && <small className="topology-review-count">{pendingReviews.length} question{pendingReviews.length === 1 ? "" : "s"}</small>}</h3>
          <p>We’ll ask about unclear spots; no circuit theory terms needed.</p>
        </div>
        <button type="button" className="topology-toggle" onClick={() => {
          setExpanded((value) => !value);
          if (expanded && advanced) {
            setAdvanced(false);
            onAdvancedChange?.(false);
          }
        }}>
          {expanded ? "Close check" : "Quick check"}
        </button>
      </div>
      {expanded && <>
      {pendingReviews.length === 0 ? <p className="topology-edit-hint">No specific unclear spot was detected. Check that the circuit shown matches your picture.</p> : <div className="topology-review-items" aria-label="Connections needing review">
        <h4>Quick questions</h4>
        {pendingReviews.map((item) => {
          const endpoints = (Array.isArray(item.endpoints) ? item.endpoints : [])
            .filter((endpoint) => endpoint?.component && endpoint?.terminal);
          const componentItem = item.kind === "component" || Boolean(item.component);
          const canAnswer = endpoints.length === 2;
          return <article className="topology-review-item" key={item.id}>
            <div>
              <strong>{componentItem ? `What is ${item.component}?` : canAnswer ? "Do these ends connect by a wire?" : "Please check the circuit connections."}</strong>
              {item.reason && <p>{item.reason}</p>}
              {componentItem && <div className="topology-answer-actions component-type-actions">
                {["resistor", "bulb", "battery", "wire"].map((type) => <button type="button" key={type}
                  onClick={() => onReviewComponentType?.(item, type)}>{type}</button>)}
                <button type="button" className="topology-skip" onClick={() => onReviewAnswer?.(item, null)}>Not sure</button>
              </div>}
              <div className="topology-review-endpoints">
                {endpoints.slice(0, 2).map((endpoint) => <button type="button" key={`${endpoint.component}::${endpoint.terminal}`}
                  onClick={() => { setExpanded(true); onReviewEndpointSelect?.(endpoint); }}>
                  {endpoint.component}, end {endpoint.terminal}
                </button>)}
              </div>
            </div>
            {!componentItem && canAnswer ? <div className="topology-answer-actions">
              <button type="button" onClick={() => onReviewAnswer?.(item, true)}>Yes</button>
              <button type="button" onClick={() => onReviewAnswer?.(item, false)}>No</button>
              <button type="button" className="topology-skip" onClick={() => onReviewAnswer?.(item, null)}>Skip</button>
            </div> : !componentItem && <button type="button" className="topology-skip" onClick={() => { setAdvanced(true); onAdvancedChange?.(true); }}>Open editor</button>}
          </article>;
        })}
      </div>}
      <button type="button" className="topology-advanced-toggle" onClick={() => { setAdvanced((value) => !value); onAdvancedChange?.(!advanced); }}>
        {advanced ? "Hide advanced connection editor" : "Advanced: edit all connections"}
      </button>
      {advanced && <>
      <p className="topology-edit-hint">Choose one end, then another to connect them. Same-color labels on the image show the current connections.</p>
      <div className="topology-node-summary">
        {nodes.map((node) => (
          <div className="topology-node-group" key={node.id} style={{ "--node-color": nodeColors.get(node.id) }}>
            <b>{node.id}</b>
            <div className="topology-terminal-chips">
              {node.terminals.map((endpoint) => {
                const selected = endpoint.component === selectedTerminal?.component
                  && endpoint.terminal === selectedTerminal?.terminal;
                return <button
                  type="button"
                  key={`${endpoint.component}::${endpoint.terminal}`}
                  className={`topology-terminal-chip${selected ? " is-selected" : ""}`}
                  onClick={() => onTerminalSelect(endpoint)}
                  aria-pressed={selected}
                >
                  {endpoint.component} · {endpoint.terminal}
                </button>;
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="topology-edit-actions">
        <span>{selectedTerminal ? `Selected ${selectedTerminal.component}, end ${selectedTerminal.terminal}` : "Choose an end to move or connect."}</span>
        <button type="button" disabled={!selectedNode || selectedNode.terminals.length < 2} onClick={onSeparateTerminal}>
          Disconnect selected end
        </button>
      </div>
      </>}
      </>}
    </section>
  );
}

export default TopologyEditor;
