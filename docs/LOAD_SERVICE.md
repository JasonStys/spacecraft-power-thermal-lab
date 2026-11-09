# Review load service

The service panel separates requested housekeeping, heater and science load. It integrates interval-average requested, served and unserved watts into Wh. Intentional reserve-policy science shedding is a separate ledger: power deliberately not requested must not be relabeled as supply failure.

Expand a component to inspect contiguous deficit intervals with exact modeled `[start,end)` seconds, integrated unserved Wh and peak deficit W. Deficits above `1e-8 W` create an episode; smaller round-off stays in the integrated totals but does not create a spurious interruption. A following no-deficit modeled interval establishes observed resumed service. A deficit at the experiment end remains right-censored; no recovery is invented.

The complete-run ledger accompanies JSON/HTML and CLI history under the content hash. Existing interval CSV keeps its dimensioned flow columns. Service intervals do not establish continuous thermal-limit excursions, hardware reliability or real spacecraft operating safety. All inputs are fictional; the original C++/Python sample comparison and independent electrical/thermal energy audits remain mandatory.
