---
description: OpenAPI 3.1 contract rules. Use when creating or editing an API spec, adding or changing HTTP endpoints, or configuring spec linting.
---

# OpenAPI

## Spec-first, framework-agnostic
- MUST treat one committed `openapi.yaml` (or `.json`) as the API contract, at `api/openapi.yaml`. Design or change the spec first, review it, then implement handlers to match.
- MUST target `openapi: 3.1.x`. Schema Objects are JSON Schema Draft 2020-12. Treat all 3.1.* patches alike.
- MUST NOT depend on a Rust web framework for the contract. Leptos, Topcoat, or axum may implement it; none defines it.
- MAY generate code from the spec. Server-side spec-first generators for Rust are `(unverified)` (none researched); `progenitor` generates clients only and its 3.1 input support is `(unverified)`.
- MAY instead keep the spec in sync from code with `utoipa` 6.x (`ToSchema`, `#[utoipa::path]`, 3.1 output). Then dump `ApiDoc::openapi().to_pretty_json()` to the committed file and make CI fail on `git diff --exit-code`. The spec file remains the reviewed artifact either way.
- Leptos `#[server]` functions are not part of the REST contract. Expose a public JSON API through separate axum handlers.

## Standard fields only
- MUST NOT use `x-` vendor extensions. Express governance with standard fields.
- MUST include `info.title`, `info.version`, `info.description`, `info.contact`, `info.license`, and `servers`.
- MUST give every operation a unique `operationId`, a `summary`, at least one `tag`, and a `security` declaration (root default or per-operation override).
- MUST document 4xx and 5xx responses using one shared error schema in `components.schemas`. Never leak internals in examples.
- MUST use named `components.schemas` with `$ref`; no inline anonymous object schemas on public operations. Fail on unresolved `$ref`.
- MUST mark retired operations `deprecated: true` before removal. Never remove silently.
- MUST version in the URL path (`/v1/...`). A breaking change gets a new version prefix.
- MUST paginate every list operation (`limit` with a documented maximum, plus a cursor or offset).
- SHOULD prefer explicit named actions over generic CRUD when an operation has side effects, and use distinct request/response schemas per operation.

## Lint in CI
- MUST lint the committed file with one linter: Spectral or Vacuum (Vacuum reads Spectral rulesets). Do not run several.
- MUST keep one ruleset, `.spectral.yaml`, that extends `spectral:oas` and encodes the standard-field rules above.
- MUST pin the linter version (npm lockfile, Docker tag or digest).

```yaml
# .spectral.yaml
extends: ["spectral:oas"]
rules:
  info-contact: error
  info-description: error
  info-license: error
  operation-description: warn
  operation-operationId: error
  operation-operationId-unique: error
  operation-tags: error
  oas3-unused-component: warn
```
```sh
spectral lint api/openapi.yaml --ruleset .spectral.yaml --fail-severity=warn
```
- Vacuum flag names for CI (`--fail-severity`, ruleset flag, junit output) are `(unverified)`; check `vacuum lint --help` before wiring.
- Redocly CLI (`npx @redocly/cli lint`) is an alternative with built-in rulesets; its exit-code semantics are `(unverified)`.
- Changing the spec is a public-API change: list it in the OpenSpec change before implementing (see `09-module-boundaries.md`).

Source: `docs/research/rust-web-stack.md` section 4. https://spec.openapis.org/oas/v3.1.1.html , https://github.com/stoplightio/spectral , https://github.com/daveshanley/vacuum , https://github.com/juhaku/utoipa . The governance list is a recommendation, not spec text.
