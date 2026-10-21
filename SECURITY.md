# Security policy

Created by Jason Stys. This is a local-only educational simulator, not an authenticated hosted platform or spacecraft control system.

## Supported boundary

Use the latest reviewed release on a supported OS. The service binds only IPv4 loopback, checks exact Host and relevant Origin/Fetch Metadata, exposes no mutation/upload routes, constrains query sizes and values, and confines bundled assets without following symlinks outside the asset root. A restrictive CSP disallows remote script execution, frames, plugins and connections to outside services. Labels and static report content are escaped. There are no advertisements, analytics, cookies, external fonts, account systems or AI API calls.

The native worker is a fixed subprocess, with bounded inputs/outputs, timeout and numeric-shape checks; no input supplies commands, executable paths or compiler flags. The Python implementation and independently reconstructed energy ledgers must agree before results are presented. These checks do not make untrusted arbitrary code executable safely; arbitrary code execution is not a feature. Local JSON is data only. Source imports are CLI-only and bounded. The loopback server is not designed to resist malicious local administrators or unlimited local denial-of-service requests.

SQL uses bound values, hash-verified identities, transactions and immutable-record triggers. This is not encryption or protection against someone with OS access. Optional histories, exported reports and opt-in browser preferences are private local data; Git excludes databases, secret-like files and build outputs. No application operator receives them, but the user's OS, backup software, browser extensions and file-sharing choices are outside this app's control.

Workflows use pinned action revisions, least-privilege tokens, no persisted checkout credentials, no secret-dependent pull-request execution, and no Actions artifact/cache uploads. Release packaging is manually dispatched and gated on the exact successful source SHA. Dependencies are locked and audited; zero known findings is time-specific and is not a security guarantee. Portable apps are unsigned/unnotarized. Verify digests and follow OS policy; do not disable protection to run them.

## Excluded uses

Do not expose the server through a public bind/reverse proxy, use it for real vehicle control, connect hardware, upload private telemetry to public issues, or interpret synthetic thresholds as operational safety limits. There is no flight certification, measured battery/radiator validation, radiation model, real orbital environment or cybersecurity certification.

## Reporting

Use the repository's private vulnerability reporting if available, or contact [Jason Stys through the profile](https://github.com/JasonStys) to arrange a private channel. Public issues should contain only synthetic reproductions, affected version and non-sensitive diagnostics. Never include credentials, private histories, personal information or real mission data. A report does not authorize testing systems outside this local application.
