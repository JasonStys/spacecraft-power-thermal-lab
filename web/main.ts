/** HELIO local power/thermal interface by Jason Stys.
 * Functions: controls, load, render, replay, compare. State: report, settings, controller, index, pinned, celsius.
 * Definition/variable lines: docs/CODE_INDEX.md. Dynamic text is escaped; no untrusted SVG/HTML execution.
 */
import {
  bounded,
  choices,
  defaults,
  display,
  escape,
  isReport,
  parsePreferences,
  plot,
  scenarios,
  temperature,
  type Report,
  type Settings,
} from "./contracts";
import "./style.css";
const app = document.querySelector<HTMLDivElement>("#app")!;
const storageKey = "power-thermal-preferences-v1";
let settings = { ...defaults },
  remember = false,
  celsius = false,
  index = 0;
let report: Report | null = null,
  pinned: Report | null = null,
  controller: AbortController | null = null;
try {
  const saved = parsePreferences(localStorage.getItem(storageKey));
  if (saved) {
    settings = saved;
    remember = true;
  }
} catch {
  /* Optional local preferences never block simulation. */
}
app.innerHTML = `<header class="top"><a class="brand" href="#workspace"><span aria-hidden="true">☼</span> HELIO <small>/ SUBSYSTEM LAB</small></a><nav aria-label="Project"><a href="#method">Model & limits</a><a href="https://github.com/JasonStys/spacecraft-power-thermal-lab" rel="noreferrer">Source ↗</a><a href="https://github.com/JasonStys" rel="noreferrer">Jason Stys ↗</a></nav></header><main id="workspace"><section class="hero"><div><p class="eyebrow">01 / ENERGY IN · HEAT OUT · EVIDENCE ALWAYS</p><h1>Every watt becomes<br><em>a trade-off.</em></h1><p class="intro">Follow a fictional spacecraft through light, darkness and changing demand. Explore what the battery can supply—and where the heat goes.</p></div><aside class="mission-card"><span class="tag">C++20 / INDEPENDENT PYTHON CHECK</span><div class="orbit" aria-hidden="true"><span>☼</span><i></i><b>▣</b></div><p>One body. One battery.<br>Explicit assumptions, not mission predictions.</p></aside></section><section class="controls" aria-label="Simulation settings"><div id="controls"></div><label class="remember"><input id="remember" type="checkbox">Remember these controls on this device</label></section><p id="status" role="status" aria-live="polite">Preparing the experiment…</p><section id="evidence" hidden></section><section id="method" class="method"><p class="eyebrow">METHOD / THE MODEL IS PART OF THE RESULT</p><h2>A balanced ledger is a starting point.<br>Not a spacecraft qualification.</h2><div class="method-grid"><article><h3>01 · Allocate honestly</h3><p>Solar generation feeds requested loads. Bounded battery charge/discharge covers surplus or deficit with explicit losses. Housekeeping takes priority over heater, then science. Intentional science shedding is separate from unserved demand.</p></article><article><h3>02 · Follow the heat</h3><p>One lumped body absorbs imposed environmental heat, actual load dissipation and battery loss, then radiates to a fixed ideal sink. RK4 advances kelvin; control decisions are held over each interval.</p></article><article><h3>03 · Keep the limits visible</h3><p>Every numerical sample is compared with an independent Python model; both energy balances are audited. This does not validate real batteries, geometry, orbital eclipses or spacecraft safety.</p></article></div><p><a href="https://github.com/JasonStys/spacecraft-power-thermal-lab/blob/main/docs/USER_GUIDE.md" rel="noreferrer">User guide ↗</a> · <a href="https://github.com/JasonStys/spacecraft-power-thermal-lab/issues" rel="noreferrer">Help / report an issue ↗</a></p></section></main><footer>Designed and engineered by <a href="https://github.com/JasonStys" rel="noreferrer">Jason Stys</a><span>INVENTED · OFFLINE · NO AFFILIATION OR ENDORSEMENT</span></footer>`;

/** Build finite selectors with descriptive units; no arbitrary file/device/model controls. */
function controls(): void {
  document.querySelector("#controls")!.innerHTML =
    `<label>Scenario<select id="scenario">${Object.entries(scenarios)
      .map(
        ([key, label]) =>
          `<option value="${key}" ${key === settings.scenario ? "selected" : ""}>${label}</option>`,
      )
      .join(
        "",
      )}</select></label>${(["battery", "policy", "step", "heater"] as const).map((key) => `<label>${{ battery: "Battery capacity / Wh", policy: "Science-load policy", step: "Integration step / s", heater: "Thermostat request" }[key]}<select id="${key}">${choices[key].map((value) => `<option value="${value}" ${settings[key] === value ? "selected" : ""}>${key === "policy" ? (value ? "Reserve-aware" : "Always requested") : key === "heater" ? (value ? "Hysteresis enabled" : "Disabled") : value}</option>`).join("")}</select></label>`).join("")}<button id="run" class="primary">Run experiment ↗</button>`;
  for (const key of ["scenario", "battery", "policy", "step", "heater"] as const)
    document.querySelector<HTMLSelectElement>(`#${key}`)!.addEventListener("change", (e) => {
      settings = {
        ...settings,
        [key]:
          key === "scenario"
            ? (e.target as HTMLSelectElement).value
            : Number((e.target as HTMLSelectElement).value),
      };
      void load();
    });
  document.querySelector("#run")!.addEventListener("click", () => void load());
}

/** Abort superseded requests and hide stale evidence; native/reference failures never look successful. */
async function load(): Promise<void> {
  controller?.abort();
  const current = new AbortController();
  controller = current;
  const status = document.querySelector<HTMLElement>("#status")!,
    evidence = document.querySelector<HTMLElement>("#evidence")!;
  evidence.hidden = true;
  status.textContent = "Running C++ and independent Python verification…";
  if (remember)
    try {
      localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch {
      /* Optional storage. */
    }
  try {
    const query = new URLSearchParams(Object.entries(settings).map(([k, v]) => [k, String(v)]));
    const response = await fetch(`/api/run?${query}`, {
      signal: current.signal,
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Analysis unavailable");
    const value: unknown = await response.json();
    if (!isReport(value)) throw new Error("Invalid evidence");
    if (controller !== current) return;
    report = value;
    index = 0;
    render();
    evidence.hidden = false;
    status.textContent = "Verified: C++ and Python samples agree. Both energy balances passed.";
  } catch {
    if (current.signal.aborted || controller !== current) return;
    report = null;
    status.innerHTML = `Could not verify experiment. <button id="retry">Try again</button>`;
    document.querySelector("#retry")!.addEventListener("click", () => void load());
  }
}

/** Render full-run summaries and pinned evidence separately from the currently selected interval. */
function render(): void {
  if (!report) return;
  const r = report;
  const query = new URLSearchParams(Object.entries(r.settings).map(([k, v]) => [k, String(v)]));
  document.querySelector("#evidence")!.innerHTML =
    `<div class="metric-label">COMPLETE EXPERIMENT / NOT THE SELECTED INTERVAL</div><div class="metrics">${[
      ["FINAL BATTERY", display(r.totals.final_soc * 100, 1), "% SOC"],
      ["UNSERVED DEMAND", display(r.totals.unserved_wh), "Wh"],
      ["SCIENCE SHED", display(r.totals.science_shed_wh), "Wh intentional"],
      [
        "BODY RANGE",
        `${display(temperature(r.totals.min_temperature_k, celsius), 1)}–${display(temperature(r.totals.max_temperature_k, celsius), 1)}`,
        celsius ? "°C sampled" : "K sampled",
      ],
    ]
      .map(
        ([label, value, unit]) =>
          `<article><p>${label}</p><strong>${value}</strong><small>${unit}</small></article>`,
      )
      .join(
        "",
      )}</div><section class="panel"><div class="section-head"><div><p class="eyebrow">02 / COUPLED STATE REPLAY</p><h2>Light changes. The budget follows.</h2></div><label class="toggle"><input id="celsius" type="checkbox" ${celsius ? "checked" : ""}>Display °C</label></div><p>Each record contains interval-average flows and the state at its end. Curves connect simulated samples—not continuous extrema. All stored temperatures remain kelvin.</p><div class="replay"><button id="previous" aria-label="Previous interval">←</button><label for="sample">Interval ending <output id="time-label"></output></label><input id="sample" type="range" min="0" max="${r.samples.length - 1}" value="${index}" step="1"><button id="next" aria-label="Next interval">→</button><button id="end">Jump to end</button></div><div id="state" class="state-grid"></div><div class="plots"><article><h3>Battery reserve</h3><div id="soc-chart"></div></article><article><h3>Body temperature</h3><div id="temperature-chart"></div></article></div><article class="power-plot"><h3>Available, requested and served power</h3><div id="power-chart"></div></article><p class="plot-note">The complete CSV provides exact values for every sampled interval; the slider below the controls selects one record without changing the experiment.</p></section><section class="panel"><div class="section-head"><div><p class="eyebrow">03 / ALLOCATION & ACCOUNTING</p><h2>No invented watts.</h2></div><span class="tag">HOUSEKEEPING → HEATER → SCIENCE</span></div><div id="allocation"></div><div class="audit"><div><p>Electrical residual / max absolute</p><strong>${display(r.totals.max_electric_residual_w, 9)} W</strong></div><div><p>Thermal residual / max absolute</p><strong>${display(r.totals.max_thermal_residual_w, 9)} W</strong></div><div><p>Outside configured temperature band</p><strong>${escape(r.totals.outside_limit_samples)} samples</strong></div></div><p>Residuals are bookkeeping checks of the stated equations (gate: 0.000001 W). Values shown are rounded. A balanced ledger is not evidence of real physical accuracy or safety. Temperature-band counts are sampled endpoints, not time outside limits.</p></section><section class="panel"><div class="section-head"><div><p class="eyebrow">04 / COMPARE EXPLICIT TRADE-OFFS</p><h2>Protect reserve. Count the science forgone.</h2></div><button id="pin">Pin current result</button></div><p>Pin a result, then change a policy or scenario. This is an in-memory comparison; different cases are not controlled policy experiments.</p><div id="comparison"></div></section><section class="panel"><p class="eyebrow">05 / REPRODUCIBLE EVIDENCE</p><h2>The assumptions travel with the output.</h2><p>Source: ${escape(r.provenance.source)}. ${escape(r.provenance.reference)}.</p><div class="downloads">${["json", "csv", "html", "input"].map((format) => `<a href="/api/report?${query}&format=${format}" download>${format === "input" ? "Input JSON" : format.toUpperCase() + " report"} ↓</a>`).join("")}</div><p class="digest">REPORT SHA-256<br>${escape(r.id)}</p><details><summary>Parameters, provenance and model limits</summary><pre>${escape(JSON.stringify(r.input.config, null, 2))}</pre><ul>${r.limitations.map((v) => `<li>${escape(v)}</li>`).join("")}</ul></details></section>`;
  document.querySelector("#sample")!.addEventListener("input", (e) => {
    index = Number((e.target as HTMLInputElement).value);
    replay();
  });
  document.querySelector("#previous")!.addEventListener("click", () => {
    index = Math.max(0, index - 1);
    replay();
  });
  document.querySelector("#next")!.addEventListener("click", () => {
    index = Math.min(r.samples.length - 1, index + 1);
    replay();
  });
  document.querySelector("#end")!.addEventListener("click", () => {
    index = r.samples.length - 1;
    replay();
  });
  document.querySelector("#celsius")!.addEventListener("change", (e) => {
    celsius = (e.target as HTMLInputElement).checked;
    render();
    document.querySelector<HTMLInputElement>("#celsius")!.focus();
  });
  document.querySelector("#pin")!.addEventListener("click", () => {
    pinned = r;
    compare();
  });
  replay();
  compare();
}

/** Show interval-held decisions and actual flows; initial state points are included on state plots. */
function replay(): void {
  if (!report) return;
  const r = report,
    s = r.samples[index],
    c = r.input.config;
  if (!s) return;
  document.querySelector<HTMLInputElement>("#sample")!.value = String(index);
  document.querySelector("#time-label")!.textContent =
    `${display(s.time_s, 0)} s (Δ ${display(s.dt_s, 0)} s)`;
  document.querySelector("#state")!.innerHTML =
    `<article class="sun-state"><p class="eyebrow">${s.solar_flux_w_m2 > 0 ? "ILLUMINATED" : "DARKNESS"}</p><strong>${display(s.solar_w, 1)} <small>W solar</small></strong><p>${display(s.solar_flux_w_m2, 0)} W/m² imposed flux</p></article><article><p class="eyebrow">CHEMICAL BATTERY ENERGY</p><strong>${display(s.energy_wh, 2)} <small>/ ${display(c.battery_wh, 0)} Wh</small></strong><svg viewBox="0 0 200 8" role="img" aria-label="Battery state of charge"><rect class="bar-bg" width="200" height="8"/><rect class="bar-fill" width="${bounded(s.energy_wh / c.battery_wh, 1) * 200}" height="8"/></svg><p>${display((s.energy_wh / c.battery_wh) * 100, 1)}% SOC · ${s.payload_enabled ? "Science requested" : "Science intentionally shed"}</p></article><article><p class="eyebrow">SINGLE BODY</p><strong>${display(temperature(s.temperature_k, celsius), 2)} <small>${celsius ? "°C" : "K"}</small></strong><p>${s.heater_on ? "Heater requested" : "Heater not requested"} · ${display(s.heater_served_w, 2)} W actually served</p></article>`;
  const times = [0, ...r.samples.map((v) => v.time_s)];
  document.querySelector("#soc-chart")!.innerHTML = plot(
    "Battery reserve",
    times,
    [
      {
        label: "State of charge",
        className: "stored",
        values: [c.initial_soc * 100, ...r.samples.map((v) => (v.energy_wh / c.battery_wh) * 100)],
      },
    ],
    "% SOC",
    s.time_s,
  );
  document.querySelector("#temperature-chart")!.innerHTML = plot(
    "Body temperature",
    times,
    [
      {
        label: "Modeled body",
        className: "thermal",
        values: [
          temperature(c.initial_temp_k, celsius),
          ...r.samples.map((v) => temperature(v.temperature_k, celsius)),
        ],
      },
    ],
    celsius ? "°C" : "K",
    s.time_s,
    false,
  );
  document.querySelector("#power-chart")!.innerHTML = plot(
    "Power interval averages",
    r.samples.map((v) => v.time_s),
    [
      { label: "Solar generation", className: "solar", values: r.samples.map((v) => v.solar_w) },
      { label: "Requested", className: "load", values: r.samples.map((v) => v.requested_w) },
      { label: "Served", className: "stored", values: r.samples.map((v) => v.served_w) },
    ],
    "W / interval averages",
    s.time_s,
  );
  const entries = [
    ["Requested after policy", s.requested_w],
    ["Actually served", s.served_w],
    ["Unserved demand", s.unserved_w],
    ["Intentional science shedding", s.shed_requested_w],
    ["Heater served", s.heater_served_w],
    ["Science served", s.payload_served_w],
    ["Battery charge input", s.charge_in_w],
    ["Battery bus discharge", s.discharge_bus_w],
    ["Battery conversion heat", s.battery_loss_w],
    ["Surplus rejected outside body", s.spill_w],
    ["Total body heat input", s.heat_in_w],
    ["Net radiation / RK4 average", s.radiation_w],
  ];
  document.querySelector("#allocation")!.innerHTML =
    `<div class="table-scroll" role="region" aria-label="Selected interval power allocation" tabindex="0"><table><thead><tr><th>Quantity / interval ending ${display(s.time_s, 0)} s</th><th>Power / W</th></tr></thead><tbody>${entries.map(([label, value]) => `<tr><td>${label}</td><td>${display(value, 4)}</td></tr>`).join("")}</tbody></table></div>`;
}

/** Compare explicitly pinned complete-run outcomes, never silently claim unlike profiles are comparable. */
function compare(): void {
  document.querySelector("#comparison")!.innerHTML =
    !pinned || !report
      ? "<p>No result pinned yet.</p>"
      : `<div class="table-scroll" role="region" aria-label="Pinned result comparison" tabindex="0"><table><thead><tr><th>Complete experiment</th><th>Pinned</th><th>Current</th></tr></thead><tbody><tr><td>Case / policy / capacity</td>${[pinned, report].map((r) => `<td>${escape(r.name)} / ${r.settings.policy ? "reserve-aware" : "always requested"} / ${display(r.input.config.battery_wh, 0)} Wh</td>`).join("")}</tr>${[
          ["Final SOC / %", "final_soc", 100],
          ["Served science / Wh", "science_served_wh", 1],
          ["Intentional science shed / Wh", "science_shed_wh", 1],
          ["Unserved requested energy / Wh", "unserved_wh", 1],
        ]
          .map(
            ([label, key, scale]) =>
              `<tr><td>${label}</td>${[pinned!, report!].map((r) => `<td>${display(r.totals[key as keyof typeof r.totals] * Number(scale), 3)}</td>`).join("")}</tr>`,
          )
          .join("")}</tbody></table></div>`;
}
controls();
document.querySelector<HTMLInputElement>("#remember")!.checked = remember;
document.querySelector("#remember")!.addEventListener("change", (e) => {
  remember = (e.target as HTMLInputElement).checked;
  try {
    if (remember) localStorage.setItem(storageKey, JSON.stringify(settings));
    else localStorage.removeItem(storageKey);
  } catch {
    /* Optional preference storage. */
  }
});
void load();
