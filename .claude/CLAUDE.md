# mrs. (formulation company site)

Not yet built. This repo is one of several `*.kelseys.site` subdomains under one project root — see the parent `kelseys.site/.claude/CLAUDE.md` for the overall layout and shared-infra conventions.

The full implementation plan — schema, business logic to port, route list, repo tree, naming, test plan, build order with checkpoints — is written out in `.claude/PLAN.md`. Read that before starting any implementation work here; don't re-derive it from scratch or re-litigate its decisions without asking.

`cli-version` (a symlink to an unrelated-looking path outside this repo) holds the old CLI tool whose formulation/costing logic `PLAN.md` describes porting — it's gitignored and reference-only, not something `app/` should import from directly.
