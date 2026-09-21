const key = (v) => JSON.stringify([v.file, v.symbol, v.metric, v.direction]);
export function metricSnapshot(violations) {
  const groups = {};
  for (const violation of violations) {
    (groups[key(violation)] ??= []).push(violation.actual);
  }
  for (const [name, values] of Object.entries(groups)) {
    const direction = JSON.parse(name)[3];
    values.sort((a, b) => direction === "min" ? a - b : b - a);
  }
  return Object.fromEntries(Object.entries(groups).sort(([a], [b]) => a.localeCompare(b)));
}

export function compareBaseline(violations, baseline) {
  const current = metricSnapshot(violations);
  const errors = [];
  for (const [name, values] of Object.entries(current)) {
    const previous = baseline[name] ?? [];
    const direction = JSON.parse(name)[3];
    for (const [index, value] of values.entries()) {
      const limit = previous[index];
      if (limit === undefined || (direction === "min" ? value < limit : value > limit)) {
        errors.push(`New/worsened metric ${name}: ${value} (baseline: ${limit ?? "none"})`);
      }
    }
  }
  return { errors, current, stale: JSON.stringify(current) !== JSON.stringify(baseline) };
}

export function validateBaseline(baseline) {
  if (!baseline || Array.isArray(baseline) || typeof baseline !== "object") throw new Error("Invalid quality baseline");
  for (const [name, values] of Object.entries(baseline)) {
    const fields = JSON.parse(name);
    if (fields.length !== 4 || !["min", "max"].includes(fields[3]) || !Array.isArray(values)
      || !values.length || values.some((v) => typeof v !== "number" || !Number.isFinite(v))) {
      throw new Error(`Invalid baseline entry: ${name}`);
    }
  }
  return baseline;
}

export function baselineExpansions(current, previous) {
  const entries = Object.entries(current).flatMap(([name, values]) => {
    const [file, symbol, metric, direction] = JSON.parse(name);
    return values.map((actual) => ({ file, symbol, metric, direction, actual }));
  });
  return compareBaseline(entries, previous).errors;
}
