/** Pure presentation and hostile-envelope contracts by Jason Stys; test/variable lines: docs/CODE_INDEX.md. */
import { expect, test } from "vitest";
import {
  bounded,
  defaults,
  display,
  escape,
  isReport,
  parsePreferences,
  plot,
  sampleKeys,
  temperature,
  totalKeys,
} from "./contracts";

/** Build a structural-only unit fixture; real physical verification is performed by integration tests. */
function fixture() {
  return {
    schema: 1,
    id: "a".repeat(64),
    name: "unit-fixture",
    input: {
      name: "unit-fixture",
      config: {
        battery_wh: 40,
        initial_soc: 0.6,
        initial_temp_k: 285,
        min_temp_k: 260,
        max_temp_k: 320,
      },
      segments: [{ duration_s: 5, solar_flux_w_m2: 0, payload_w: 0 }],
    },
    settings: { ...defaults },
    totals: Object.fromEntries(totalKeys.map((k) => [k, 0])),
    samples: [Object.fromEntries(sampleKeys.map((k) => [k, 0]))],
    provenance: { source: "synthetic unit structure", reference: "not a physics result" },
    limitations: ["Unit-only structural fixture"],
  };
}
test("text and attribute escapes are complete", () => {
  expect(escape('<img a="&\'">')).toBe("&lt;img a=&quot;&amp;&#39;&quot;&gt;");
});
test("SVG quantities clamp finite domains", () => {
  expect(bounded(-1, 100)).toBe(0);
  expect(bounded(500, 100)).toBe(100);
  expect(bounded(NaN, 1)).toBe(0);
  expect(bounded(Infinity, 1)).toBe(0);
  expect(bounded("1", 1)).toBe(0);
});
test("missing readings never masquerade as zero", () => {
  expect(display(undefined)).toBe("Not available");
  expect(display(NaN)).toBe("Not available");
  expect(display(0)).toBe("0.00");
});
test("Celsius is display-only with exact offset", () => {
  expect(temperature(273.15, true)).toBe(0);
  expect(temperature(273.15, false)).toBe(273.15);
});
test("finite preferences roundtrip", () => {
  expect(parsePreferences(JSON.stringify(defaults))).toEqual(defaults);
});
test("invalid storage and coercions are discarded", () => {
  for (const v of [
    null,
    "no-json",
    "[]",
    "{}",
    JSON.stringify({ ...defaults, battery: true }),
    JSON.stringify({ ...defaults, extra: 1 }),
  ])
    expect(parsePreferences(v)).toBeNull();
});
test("prototype names are not selectable cases", () => {
  expect(parsePreferences(JSON.stringify({ ...defaults, scenario: "toString" }))).toBeNull();
});
test("complete numeric report shape accepted", () => {
  expect(isReport(fixture())).toBe(true);
});
test("missing physical fields and totals rejected", () => {
  const v = fixture();
  delete v.totals.final_soc;
  expect(isReport(v)).toBe(false);
  expect(isReport({ ...fixture(), samples: [] })).toBe(false);
  expect(isReport({ ...fixture(), input: { ...fixture().input, config: {} } })).toBe(false);
});
test("nonfinite and malformed rows rejected", () => {
  const v = fixture();
  v.samples[0]!.temperature_k = Infinity;
  expect(isReport(v)).toBe(false);
  expect(isReport(null)).toBe(false);
});
test("plot labels escaped and degenerate values finite", () => {
  const svg = plot(
    '<script>"',
    [],
    [{ label: "<img>", className: "solar", values: [NaN, 1] }],
    "W",
    Infinity,
  );
  expect(svg).not.toContain("<script>");
  expect(svg).not.toContain("<img>");
  expect(svg).not.toMatch(/NaN|Infinity/);
  expect(svg).toContain("&lt;img&gt;");
});
test("thermal plot uses explicit adaptive range", () => {
  const svg = plot(
    "Temperature",
    [0, 5],
    [{ label: "body", className: "thermal", values: [285, 286] }],
    "K",
    5,
    false,
  );
  expect(svg).toContain("285.0");
  expect(svg).toContain("286.0");
});
