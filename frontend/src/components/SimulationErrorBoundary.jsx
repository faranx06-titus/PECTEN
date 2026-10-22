import { Component } from "react";

class SimulationErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Simulation view failed to render:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <section className="render-error-panel" role="alert">
        <h3>The circuit was analyzed, but its view could not be displayed.</h3>
        <p>The backend completed analysis. A frontend display error stopped the simulation view from rendering.</p>
        <details><summary>Display error details</summary><pre>{this.state.error.message}</pre></details>
        <button type="button" onClick={this.props.onReset}>Return to the upload page</button>
      </section>
    );
  }
}

export default SimulationErrorBoundary;
