# VideoRenderer Dependencies

Immutable application dependencies for [marcmy/VideoRenderer](https://github.com/marcmy/VideoRenderer). Get the recommended lightweight installer from the [renderer release page](https://github.com/marcmy/VideoRenderer/releases/latest).

## Packages

- RIFE runtime: common runtime DLLs plus GPU packs for SM75, SM86, SM89 and SM120.
- RIFE models: supported prepared ONNX variants and reusable encoder models.
- Maxine: application runtime components and their original NVIDIA notices.

These are application runtime packages, not a general SDK mirror. NVIDIA components retain their original terms; the renderer's GPL does not relicense them. RIFE model packages retain their original licenses. Each immutable release includes its component manifest, original provenance, sizes and SHA-256 hashes. The renderer's `dependencies.lock.json` selects exact assets; dependency resolution never uses moving `latest` URLs.

## Publishing and maintenance

Publishing is separate from renderer updates. From the authoritative VideoRenderer checkout, review and push clean committed source, then run `./dev.ps1 dependencies -Component rife-runtime` (or `rife-models`, `maxine`). Existing GitHub credentials must permit editing this repository's workflow configuration; no credential is embedded in packages or supplied to CI.

The command preserves this repository's reviewed external action pins, binds every source checkout and both actual builder definitions to the approved renderer SHA, and dispatches a fixed source/configuration approval tag. Manual inputs cannot select another executable commit. Matching approvals and unchanged immutable packages are reused. Conflicting configuration/tag content fails safely; tags and published package bytes are never replaced.

The publisher's structural/security template is maintained in `VideoRenderer/tools/Dev/DependencyRepository.yml`. This repository owns external action versions. Dependabot proposes grouped weekly action updates and updates the small YAML-validation dependency. Approved renderer/build-workflow SHAs are excluded from bot updates. Fast PR/push validation checks YAML syntax, source bindings, action pins, credential persistence and permissions without downloading or rebuilding runtime packages.

Pre-merge dependency publication remains supported so new verified lock-file pins can pass renderer CI before merge. For unapproved experiments, use the renderer repository's existing runtime/model builders on a review branch; those produce artifacts without publishing here.

After publishing a changed component, use the renderer's existing dependency `plan` and `lock` commands, review the new pins and commit them. Architecture detection, license/integrity checks, installation and rollback are handled by the renderer installer. Existing immutable packages are retained independently of renderer release retention.

See [SECURITY.md](SECURITY.md) for private reporting and the publishing invariants.
