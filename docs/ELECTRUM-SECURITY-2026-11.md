# ElectrumX backend maintenance — November 2026

These source changes apply to Pepecoin and Whippet indexers. They do not change
the database schema, transaction-signing rules or Core consensus validation.
The custom-fork version banner remains ElectrumX 1.18.0.

- Pin Python 3.13.18 and websockets 17.4, including the upstream
  [empty-fragment memory-exhaustion fix](https://github.com/python-websockets/websockets/security/advisories/GHSA-6m5v-9gmr-5665).
  Keep aiohttp 3.14.5 and multidict 7.2.1 in the reviewed dependency set.
  Enforce the same minimums for direct Python installs; Python 3.11 or newer is
  required by these patched dependencies.
- Remove the base image's pip before copying builder packages, avoiding stale
  installer metadata from two different pip versions in the runtime.
- Backport [upstream peer-discovery hardening](https://github.com/spesmilo/electrumx/pull/402):
  validate announcements, bound host/peer counts and hostname lengths, reject
  non-public peers, handle DNS Unicode failures and correct peer-rate-limit expiry.
- Include Whippet mainnet identity, synthetic legacy/AuxPoW parser coverage,
  and real genesis/post-activation block fixtures checked against two Core nodes.
  Pepecoin and Whippet require separate databases and Core RPC connections.

Tests cover bounded fragment rejection and subsequent normal requests,
multidict reference release, peer input/graph limits, session-limit recovery,
both chain identities and history-compaction safety. The existing CI unit-test
step discovers the new `tests/test_*.py` files.

Both live indexers were updated and checked separately, Whippet first. Public TLS,
Core-anchored headers, transaction IDs/Merkle proofs and wallet queries passed.
Those operational checks used staged runtime images; this source revision and
any registry image built from it require their own build and CI verification.
No previously published registry digest is replaced by this source push.

The checked runtime images still have vendor-unfixed OS package findings. No
available fixed versions were reported by the scan at the time of the audit;
that is not a claim of zero vulnerabilities. Keep reviewing advisories and
rebuilding/retesting. The optional dashboard retains its private Docker RPC
connection; admin port 8000 must not be published on the host.
