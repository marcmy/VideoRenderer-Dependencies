# Security Policy

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/marcmy/VideoRenderer-Dependencies/security/advisories/new). Include the affected component, source/release identifiers, and a minimal reproduction. Do not publish credentials or private media in an issue.

## Scope and trust boundaries

This public repository distributes immutable Maxine, RIFE model, TensorRT and CUDA runtime components for VideoRenderer. Its publishing workflow, approval configuration, release manifests and download integrity are security-sensitive. Renderer/runtime implementation remains in [VideoRenderer](https://github.com/marcmy/VideoRenderer).

A maintainer with workflow-file write authority may approve a specific reviewed renderer commit. A manual dispatch argument is data and cannot independently authorize executable source. Pre-merge validation runs in an unprivileged PR/branch context. Dependency publication is a separate approved operation.

## Required invariants

- Checkouts, actual reusable builder definitions and publication scripts use the same literal approved source SHA.
- The requested SHA is checked before planning/building; malformed and unapproved inputs fail closed.
- Only the publishing job receives repository-content write permission. Validation must not gain publishing credentials or authority over trusted caches.
- Approval tags are never moved or replaced. Separate source/configuration identities preserve requests during concurrent maintenance.
- Runtime/model assets use exact immutable references and pinned SHA-256 hashes, retaining license notices and original provenance. Changed bytes never overwrite an immutable package.

## Assessment and reporting

Report concrete routes that violate these boundaries or permit unauthorized source execution, publication, cache/artifact poisoning, or acceptance of modified downloads. Manual dispatch, read-only content permissions and checksum checks alone do not establish that source execution is authorized. Include required privileges and the specific trusted consumer affected.

No finding category is excluded by this policy. Vendor-component findings may also require upstream coordination; the integrity of the packages distributed here remains in scope.
