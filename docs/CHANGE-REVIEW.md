# Separate security diffs

The initial public history deliberately separates the source import, production
history guard, security packages, dashboard access hardening, and test fixes.
The root import is a historical baseline, not a recommended deployable release.
Use current reviewed `main` for the complete stack.

## Optional dashboard: security-patched container runtime

Commit: [d02676e](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793)

[Download the exact patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793.patch)

**Optional:** wallets and direct Electrum RPC clients do not need this component.
Updates the separate dashboard's package base, preserves UID-33 data and runtime
secrets, restricts HTTP file access, and verifies populated pages and restart.
Does not change daemon code or data. See [setup, tests and scope](DASHBOARD.md).
The workflow/publication changes are separate from this security diff.

## Standalone runtime packaging and dependency review

Commit: [c9b8187](https://github.com/lostinbtc/pepecoin-electrumx/commit/c9b8187)

Moves daemon compilation into a separate build stage, constrains its Python runtime
dependencies, pins base-image digests, and removes unused installer/build tooling.
The optional dashboard refreshes Debian packages and removes development headers.
This does not change Electrum protocol code or database format. Full scan findings
and publication limits are disclosed in [release security](RELEASE-SECURITY.md).

The release/test pipeline is separate in [bb6a0d2](https://github.com/lostinbtc/pepecoin-electrumx/commit/bb6a0d2).
Dashboard branding and neutral legacy test naming are separate in
[ad7cd31](https://github.com/lostinbtc/pepecoin-electrumx/commit/ad7cd31).
The previously shared compatibility-patch README and URL are retained unchanged.

## Our split dashboard: PHP and Brotli package patch

Commit: [6d569b5](https://github.com/lostinbtc/pepecoin-electrumx/commit/6d569b56d6c839839391d09624214df4465355bf)

[Download this commit as a patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/6d569b56d6c839839391d09624214df4465355bf.patch)

Changes the bookworm dashboard build to require patched PHP and Brotli revisions.
It does not change Electrum RPC, databases, startup compaction, or authentication.
This diff applies to our split dashboard build, not the original trixie image.

## Our split dashboard: authentication hardening

Commit: [bf71ffb](https://github.com/lostinbtc/pepecoin-electrumx/commit/bf71ffb4350e0d842a41685874a0ab9f49f42fd6)

[Download this commit as a patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/bf71ffb4350e0d842a41685874a0ab9f49f42fd6.patch)

Requires a runtime password, fails closed if it is missing or too short, disables
browser error details, and protects source-directory access. This is independent
of the package update. Keep the dashboard private; this is not a complete security
audit or permission to expose the legacy administrative application publicly.

## Original combined image: Brotli-only compatibility patch

Commit: [73f4421](https://github.com/lostinbtc/pepecoin-electrumx/commit/73f442150d8cc50aa5791aeff51798c5a4fbf62b)

[Download this commit as a patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/73f442150d8cc50aa5791aeff51798c5a4fbf62b.patch)

Adds `patches/emgi-brotli/`: an independent build context deriving from the exact
supplied digest, with a trixie Brotli revision guard. It does not require adopting
our Compose layout, dashboard changes, or history guard. Follow the instructions
in that folder and retain your own existing deployment configuration.

These patch files are review/application artifacts, not Docker images or registry
digests. Inspect target paths and your base before applying any patch. Do not apply
all changes merely to fix the single reported Brotli issue.
