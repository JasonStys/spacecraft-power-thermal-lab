/** Typed presentation contracts by Jason Stys; functions/types/variables: docs/CODE_INDEX.md.
 * Numeric SVG geometry, strict finite preferences, explicit SI-to-display conversion and escaped labels.
 */
export const scenarios = {
  "day-night-cycle": "Illumination cycle",
  "extended-eclipse": "Extended darkness",
  "payload-surge": "Scientific payload surge",
  "cold-start": "Cold start",
  "hot-soak": "Hot soak",
  "battery-full": "Full battery / spill",
  "battery-empty": "Empty battery / recovery",
  "isolated-cooling": "Analytic cooling",
  "heater-contention": "Heater power contention",
};
export const choices = { battery: [20, 40, 80], policy: [0, 1], step: [1, 5, 10], heater: [0, 1] };
export interface Settings {
  scenario: string;
  battery: number;
  policy: number;
  step: number;
  heater: number;
}
export const defaults: Settings = {
  scenario: "day-night-cycle",
  battery: 40,
  policy: 0,
  step: 5,
  heater: 1,
};
export const sampleKeys = [
  "time_s",
  "dt_s",
  "solar_w",
  "requested_w",
  "served_w",
  "unserved_w",
  "charge_in_w",
  "discharge_bus_w",
  "battery_loss_w",
  "spill_w",
  "energy_wh",
  "temperature_k",
  "heat_in_w",
  "radiation_w",
  "electric_residual_w",
  "thermal_residual_w",
  "base_served_w",
  "heater_served_w",
  "payload_served_w",
  "shed_requested_w",
  "heater_on",
  "payload_enabled",
  "solar_flux_w_m2",
  "payload_requested_w",
] as const;
export const totalKeys = [
  "duration_s",
  "final_soc",
  "min_soc",
  "min_temperature_k",
  "max_temperature_k",
  "max_electric_residual_w",
  "max_thermal_residual_w",
  "outside_limit_samples",
  "solar_wh",
  "served_wh",
  "unserved_wh",
  "spill_wh",
  "battery_loss_wh",
  "science_served_wh",
  "science_shed_wh",
  "heater_served_wh",
] as const;
export type Sample = Record<(typeof sampleKeys)[number], number>;
export type Totals = Record<(typeof totalKeys)[number], number>;
export type Configuration = Record<
  "battery_wh" | "initial_soc" | "initial_temp_k" | "min_temp_k" | "max_temp_k",
  number
> &
  Record<string, number>;
export interface Report {
  schema: 1;
  id: string;
  name: string;
  input: {
    name: string;
    config: Configuration;
    segments: { duration_s: number; solar_flux_w_m2: number; payload_w: number }[];
  };
  settings: Settings;
  totals: Totals;
  samples: Sample[];
  provenance: Record<string, string>;
  limitations: string[];
}

/** Escape every dynamic text/attribute; no external values become markup or CSS. */
export function escape(value: unknown): string {
  return String(value).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!,
  );
}
/** Clamp geometry to a finite nonnegative domain; NaN/infinity and strings never enter SVG. */
export function bounded(value: unknown, max: number): number {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.min(max, Math.max(0, value))
    : 0;
}
/** Render absent/nonfinite measurements explicitly rather than presenting them as zero. */
export function display(value: unknown, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "Not available";
}
/** Celsius is display-only; every stored/input/solver temperature remains kelvin. */
export function temperature(kelvin: number, celsius: boolean): number {
  return kelvin - (celsius ? 273.15 : 0);
}
/** Validate complete finite control values; reject unknown keys, coercion and hostile storage text. */
export function parsePreferences(text: string | null): Settings | null {
  try {
    const v: unknown = JSON.parse(text ?? "null");
    if (!v || typeof v !== "object") return null;
    const row = v as Record<string, unknown>;
    if (
      Object.keys(row).sort().join() !== Object.keys(defaults).sort().join() ||
      typeof row.scenario !== "string" ||
      !Object.hasOwn(scenarios, row.scenario)
    )
      return null;
    for (const key of ["battery", "policy", "step", "heater"] as const)
      if (typeof row[key] !== "number" || !choices[key].includes(row[key] as number)) return null;
    return row as unknown as Settings;
  } catch {
    return null;
  }
}
/** Validate the required bounded report shape before rendering trusted-service responses. */
export function isReport(value: unknown): value is Report {
  if (!value || typeof value !== "object") return false;
  const r = value as Report;
  const numeric = (obj: unknown): obj is Record<string, number> =>
    !!obj &&
    typeof obj === "object" &&
    !Array.isArray(obj) &&
    Object.values(obj).every((v) => typeof v === "number" && Number.isFinite(v));
  return (
    r.schema === 1 &&
    typeof r.id === "string" &&
    /^[a-f0-9]{64}$/.test(r.id) &&
    typeof r.name === "string" &&
    !!r.input &&
    numeric(r.input.config) &&
    ["battery_wh", "initial_soc", "initial_temp_k", "min_temp_k", "max_temp_k"].every(
      (k) => typeof r.input.config[k] === "number",
    ) &&
    r.input.config.battery_wh > 0 &&
    Array.isArray(r.input.segments) &&
    r.input.segments.length > 0 &&
    r.input.segments.length <= 32 &&
    r.input.segments.every((s) => numeric(s)) &&
    !!parsePreferences(JSON.stringify(r.settings)) &&
    numeric(r.totals) &&
    totalKeys.every((k) => typeof r.totals[k] === "number") &&
    Array.isArray(r.samples) &&
    r.samples.length > 0 &&
    r.samples.length <= 3600 &&
    r.samples.every((s) => numeric(s) && sampleKeys.every((k) => typeof s[k] === "number")) &&
    !!r.provenance &&
    typeof r.provenance === "object" &&
    typeof r.provenance.source === "string" &&
    typeof r.provenance.reference === "string" &&
    Object.values(r.provenance).every((v) => typeof v === "string") &&
    Array.isArray(r.limitations) &&
    r.limitations.every((v) => typeof v === "string")
  );
}
export interface Series {
  label: string;
  values: number[];
  className: "solar" | "load" | "stored" | "thermal";
}
/** Draw all sampled points with numerical bounds and explicit units; interpolation is visual only. */
export function plot(
  title: string,
  times: number[],
  series: Series[],
  unit: string,
  cursor: number,
  zeroBaseline = true,
): string {
  const values = series.flatMap((s) => s.values).filter(Number.isFinite);
  const lo = zeroBaseline ? Math.min(...values, 0) : Math.min(...values, values[0] ?? 0),
    hi = Math.max(...values, lo + 1),
    range = hi - lo || 1;
  const end = Math.max(...times.filter(Number.isFinite), 1);
  const x = (t: number) => 50 + bounded(t / end, 1) * 730;
  const y = (v: number) => 180 - bounded((v - lo) / range, 1) * 150;
  const paths = series
    .map(
      (s) =>
        `<polyline class="${s.className}" points="${s.values.map((v, i) => `${x(times[i] ?? 0).toFixed(2)},${y(v).toFixed(2)}`).join(" ")}"/>`,
    )
    .join("");
  return `<svg viewBox="0 0 810 220" role="img" aria-label="${escape(title)}; all simulated samples; exact values available in CSV"><line class="grid" x1="50" y1="30" x2="780" y2="30"/><line class="grid" x1="50" y1="105" x2="780" y2="105"/><line class="grid" x1="50" y1="180" x2="780" y2="180"/><text x="2" y="34">${escape(display(hi, 1))}</text><text x="2" y="184">${escape(display(lo, 1))}</text>${paths}<line class="cursor" x1="${x(cursor).toFixed(2)}" y1="22" x2="${x(cursor).toFixed(2)}" y2="185"/><text x="50" y="210">0 s</text><text x="700" y="210">${escape(display(end, 0))} s</text><text x="50" y="15">${escape(unit)}</text></svg><div class="legend">${series.map((s) => `<span class="${s.className}">${escape(s.label)}</span>`).join("")}</div>`;
}
