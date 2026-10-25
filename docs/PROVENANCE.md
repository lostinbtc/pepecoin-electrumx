# Source provenance

- ElectrumX upstream: `spesmilo/electrumx`, version 1.18.0. Copyright notices name
  Neil Booth and The Electrum developers; the MIT notice is retained.
- Pepecoin definitions and recovered changes: the combined
  `emgi2/pepecoin-electrum:1.18.0.1` image, whose listed source is
  `bachelor-emgi/electrumx-pep`. Its historical README attributes the Pepecoin
  adaptation to Pepe Enthusiast / Master Kush and later changes to bachelor-emgi.
- Dashboard: recovered ElectrumX Dashboard derived from `Mirobit/electrumx-dashboard`,
  with Michael Rotarius's MIT notice retained. Existing branding/assets retain
  their provenance; this project does not claim exclusive ownership of them.
- Pepecoin Service changes: peer-list maintenance, split deployment, startup/history
  safeguards, security package floors, and sanitized operator configuration.

Audited original multi-platform index:

```text
emgi2/pepecoin-electrum@sha256:b4325c274ce5aed5ecb42719738a1a5d25a07ef1669ad48551bd85cc6dcb284b
```

Inspected Linux/amd64 child:

```text
sha256:92052451c79c0026ff57117a4fd2b4e5b94cbc60680113f80d29245c7f0053e2
```

The image was extracted without starting its default entrypoint. Its ElectrumX
RPC/session source matches the recovered baseline. Against the running Pepecoin
Service daemon, 30 source files were identical; the differences were the peer list,
compactor exit status, and the added history guard. Packaging and startup changes
are tracked separately. This is source reconstruction, not the original Git history.

The upstream source repository returned 404 to an unauthenticated fresh request on
2026-10-25; an older indexed page identified it as public. This does not establish
whether it was deleted, renamed, or made private. The pinned image was downloadable.

Do not infer that a changed maintainer, digest, or repository name proves an image
safe. Review source, dependency versions, build context, and deployment boundaries.
