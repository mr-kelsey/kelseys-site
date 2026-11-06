# kelseys-site

One monorepo for every `*.kelseys.site` subdomain, each deployed independently. See
`.claude/CLAUDE.md` for the full layout, deploy conventions, and the "adding a new subdomain"
checklist.

## Repo map

| Directory | Subdomain | What it is |
|---|---|---|
| `mr/` | mr.kelseys.site | Personal resume/portfolio site |
| `mrs/` | mrs.kelseys.site | Kaleidoscopic Creations (formulation company) site |
| `root/` | kelseys.site | Public recipe book + admin family calendar |
| `proxy-serve/` | (all of the above) | Shared Caddy reverse-proxy/TLS |

## Working in a subset of this repo

This repo is meant to grow to 15-20 subdomains. Use `git sparse-checkout` so your working
tree only has what you're actually touching, rather than cloning everything:

```bash
git clone --no-checkout https://github.com/mr-kelsey/kelseys-site.git
cd kelseys-site
git sparse-checkout init --cone
git sparse-checkout set root mr      # whichever subdomain(s) you're working on
git checkout main
```

Change scope later without re-cloning:

```bash
git sparse-checkout add mrs          # add a directory to what's checked out
git sparse-checkout set root         # replace the checked-out set entirely
git sparse-checkout disable          # go back to everything
```

## Deploys

Each subdomain has its own path-filtered GitHub Actions workflow
(`.github/workflows/deploy-{name}.yml`) that only fires on a push to `main` touching that
site's directory, and calls the shared `.github/workflows/deploy-reusable.yml` to run tests
and SSH-trigger the droplet's deploy script. See `.claude/CLAUDE.md` for the secrets-naming
convention and how to wire up a new subdomain.

Status as of 2026-11-06: `mr`, `mrs`, and `proxy-serve` have deployed successfully from this
repo. `root` has no `ROOT_SSH_USER`/`ROOT_SSH_PRIVATE_KEY` secrets or droplet-side
`/opt/kelseys-root` yet, so `deploy-root.yml` correctly fires on a push touching `root/**`
but fails at the SSH step until that's provisioned.
