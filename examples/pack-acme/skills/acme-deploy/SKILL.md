---
name: acme-deploy
description: Acme deploy manifests and service charts. Validation, conventions, and review checklist for deploy/*.yaml and charts/acme-*. Use when changing or reviewing Acme deploy config.
---

# acme-deploy

Builds on the core `kubernetes` skill. Load both.

## Validate (offline)
```bash
helm lint charts/acme-<service>
helm template charts/acme-<service> -f deploy/<env>.yaml | kubeconform -strict -summary
```

## Conventions
- One `deploy/<env>.yaml` per environment. Values only, no templates.
- Every service sets `resources.requests`, `resources.limits`, and a `PodDisruptionBudget`.
- Image tags are immutable digests in `deploy/prod.yaml`.

## Review checklist
- Replica or resource changes in prod named in the spec.
- New env vars come from the secret store by name, never inline values.
- Probes changed together with the port they check.

## Never without approval
- Applying, syncing, or rolling back any environment. Deploys happen after merge, through GitOps.
