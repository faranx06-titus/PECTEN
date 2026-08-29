import { useState } from "react";
import {
  checkBackend,
  getDemoCircuit,
} from "./services/api";
import CircuitSimulator from "./components/CircuitSimulator";

function App() {
  const [status, setStatus] = useState("");
  const [circuit, setCircuit] = useState(null);

  const testBackend = async () => {
    try {
      const data = await checkBackend();
      setStatus(data.status);
    } catch (error) {
      setStatus("Backend connection failed");
    }
  };

  const loadCircuit = async () => {
    try {
      const data = await getDemoCircuit();
      setCircuit(data);
    } catch (error) {
      console.error(error);
      setStatus("Circuit loading failed");
    }
  };

  return (
    <div>
      <h1>PECTEN</h1>
      <p>Life to Textbooks.</p>

      <button onClick={testBackend}>
        Test Backend
      </button>

      <p>{status}</p>

      <button onClick={loadCircuit}>
        Load Demo Circuit
      </button>

      {circuit && (
        <div>
          <h2>Circuit</h2>

          <p>
            Battery: {circuit.battery.voltage}
            {circuit.battery.unit}
          </p>

          {circuit.components.map((component) => (
            <div key={component.id}>
              <h3>
                {component.type}: {component.id}
              </h3>

              <p>
                Resistance: {component.resistance} Ω
              </p>

              <p>
                Current: {component.current} A
              </p>

              <p>
                Voltage: {component.voltage} V
              </p>

              <p>
                Power: {component.power} W
              </p>
            </div>
            
          ))}
          <CircuitSimulator circuit={circuit} />
        </div>
      )}
    </div>
    
  );
}

export default App;