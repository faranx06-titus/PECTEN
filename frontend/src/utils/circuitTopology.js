const keyFor = (component, terminal) => `${component}::${terminal}`;

export function getCircuitNodes(circuit) {
  const terminals = (circuit?.components ?? []).flatMap((component) =>
    (component.terminals ?? []).map((terminal) => ({ component: component.id, terminal })));
  const terminalKeys = new Set(terminals.map(({ component, terminal }) => keyFor(component, terminal)));
  const supplied = circuit?.nodes;
  if (Array.isArray(supplied) && supplied.length) {
    const seen = new Set();
    const complete = supplied.every((node) => Array.isArray(node.terminals)
      && node.terminals.every(({ component, terminal }) => {
        const key = keyFor(component, terminal);
        if (!terminalKeys.has(key) || seen.has(key)) return false;
        seen.add(key);
        return true;
      })) && seen.size === terminalKeys.size;
    if (complete) return supplied.map((node, index) => ({ ...node, id: `N${index + 1}` }));
  }

  const parent = new Map([...terminalKeys].map((key) => [key, key]));
  const find = (key) => {
    if (!parent.has(key)) return null;
    let root = key;
    while (parent.get(root) !== root) root = parent.get(root);
    let current = key;
    while (parent.get(current) !== root) {
      const next = parent.get(current);
      parent.set(current, root);
      current = next;
    }
    return root;
  };
  const union = (a, b) => {
    const rootA = find(a);
    const rootB = find(b);
    if (rootA && rootB && rootA !== rootB) parent.set(rootB, rootA);
  };

  for (const component of circuit?.components ?? []) {
    if (component.type === "wire" && component.terminals?.length === 2) {
      union(keyFor(component.id, component.terminals[0]), keyFor(component.id, component.terminals[1]));
    }
  }
  for (const connection of circuit?.connections ?? []) {
    union(keyFor(connection.from?.component, connection.from?.terminal),
      keyFor(connection.to?.component, connection.to?.terminal));
  }

  const groups = new Map();
  for (const endpoint of terminals) {
    const root = find(keyFor(endpoint.component, endpoint.terminal));
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(endpoint);
  }
  return [...groups.values()].map((members, index) => ({ id: `N${index + 1}`, terminals: members }));
}

export function normalizeCircuitNodes(circuit) {
  const nodes = getCircuitNodes(circuit);
  const connections = nodes.flatMap((node) => node.terminals.slice(1).map((endpoint) => ({
    from: node.terminals[0],
    to: endpoint,
  })));
  return { ...circuit, nodes, connections };
}

export function assignTerminalToNode(circuit, component, terminal, selectedNodeId) {
  const nodes = getCircuitNodes(circuit).map((node) => ({
    ...node,
    terminals: node.terminals.filter((endpoint) =>
      !(endpoint.component === component && endpoint.terminal === terminal)),
  })).filter((node) => node.terminals.length);
  const targetId = selectedNodeId === "__new__"
    ? `N${Math.max(0, ...nodes.map((node) => Number(node.id.slice(1)) || 0)) + 1}`
    : selectedNodeId;
  const target = nodes.find((node) => node.id === targetId);
  const endpoint = { component, terminal };
  if (target) target.terminals.push(endpoint);
  else nodes.push({ id: targetId, terminals: [endpoint] });
  return normalizeCircuitNodes({ ...circuit, nodes });
}
