# CI/CD and GitOps

## Pipeline stages

Lint -> unit -> schema -> build -> SBOM -> vulnerability scan -> sign -> integration -> AI evaluation -> deploy to test -> end-to-end -> approval -> GitOps promotion -> post-deploy verification.

## Repository approach

- Monorepo initially for shared schemas and rapid development.
- Independent deployable services and versioned containers.
- Helm charts and environment overlays.
- GitOps reconciliation.
- Feature flags for model and automation capabilities.
- Signed container images and model artifacts.
