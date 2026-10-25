# Standalone release-candidate security review

Local scan date: 2026-10-25. Scanner: Trivy 0.76.1, freshly downloaded vulnerability
database. These are package findings, not evidence that a network attacker can
reach every affected code path. Counts can change as advisory databases change.

## Packaging changes

The daemon now uses a multi-stage build. Compilers and development headers stay
in the builder; the runtime contains the required LevelDB library and application
dependencies. pip and its bundled libraries, setuptools, wheel and packaging are
removed from the runtime because serving Electrum does not require them. Test-only
containers reinstall tooling when needed. Reviewed Python runtime dependencies
are constrained in `electrumx/requirements-runtime.txt`.

Base images are pinned by digest. Debian packages are refreshed at build time;
therefore independent builds are not promised to be bit-for-bit identical.
Release images need their own recorded registry digest and verification evidence.
Build-only artifacts and test certificates are excluded from image contexts.

The optional dashboard refreshes Debian packages and removes its unused extension
compiler/development headers. Its existing PHP/Brotli guards remain in place.
There are no application-code or database-format changes in these packaging edits.

## Local results

| Runtime image | Critical | High | High with available fix | Secret findings |
| --- | ---: | ---: | ---: | ---: |
| Daemon candidate | 0 | 44 | 0 | 0 |
| Optional dashboard candidate | 3 | 109 | 0 | 0 |

Counts are package/advisory matches, not necessarily distinct vulnerabilities.
The daemon's 44 High matches represent these eight distinct advisories:

- CVE-2025-69720 (ncurses)
- CVE-2026-16742 (systemd)
- CVE-2026-54369 (acl)
- CVE-2026-76642 (util-linux)
- CVE-2026-78408 (util-linux)
- CVE-2026-78409 (util-linux)
- CVE-2026-78410 (util-linux)
- CVE-2026-9538 (Perl)

The scanner reports no available fixed package revision for those matches in this
Debian base at scan time. This does not establish that they are harmless. Compose
also drops daemon capabilities except `DAC_OVERRIDE` (for reading restrictive
operator-owned certificate mounts) and sets `no-new-privileges`; these are defense
in depth, not a substitute for upstream fixes. Keep tracking Debian advisories and
rebuilding/retesting when fixes become available. No global ignore list was added.

## Dashboard publication hold

The dashboard **does not pass the candidate gate and is not published** by the
container workflow. Remaining Critical matches are:

- CVE-2025-7458 — `libsqlite3-0 3.40.1-2+deb12u2`, scanner status `affected`.
- CVE-2026-6653 — `libxml2 2.9.14+dfsg-1.3~deb12u6`, status `fix_deferred`.
- CVE-2023-45853 — `zlib1g 1:1.2.13.dfsg-1`, status `will_not_fix`.

These require advisory/package-specific review; scanner severity alone does not
demonstrate reachability in this dashboard. No exception was silently applied to
permit publication. Existing source-build users must evaluate their deployment;
keep the legacy administrative dashboard off the public Internet.

## Release boundaries

Candidate CI blocks detected secrets, all Critical findings, and fixable High
findings for the daemon. It publishes only explicit `-rc.N` tags and provides an
SBOM and sanitized summaries. Unfixed High findings remain visible. A stable
release needs a fresh scan, review of remaining findings, full-chain/restart
evidence for the chosen digest, and accurate integration limitations.

The third-party Discord bot was not supplied. Standard protocol checks must not
be represented as proof of that bot's end-to-end compatibility.
