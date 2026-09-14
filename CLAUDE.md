# vanzelfsprekend

Tufte-style range frames for matplotlib: spines trimmed to the data, nice-number ticks inside the data range (mizani `breaks_extended`), axis labels at the spine ends.

API idiom: call through the `ax.vzs` accessor (`ax.vzs.apply(...)`, `ax.vzs.range_frame(...)`, …), not the module functions. `import vanzelfsprekend as vzs` registers it on import; `compose.py` is the authority for the methods.

Docs sidenotes: write ordinary Markdown footnotes (`[^1]`); the `docs_hooks.py` build hook rewrites them into Tufte sidenotes. Don't hand-write sidenote HTML.

Docs styling and structure: the authority is `docs_hooks.py` (sidenotes, palette sheets) plus `theme/style.css`, not the rendered Markdown. Change the look there, not by hand-editing generated output.

## Repository rules

- `docs/superpowers/` (specs, plans, other superpowers artifacts) is local working material and is gitignored. Never commit it, and never use `git add -f` on it.

## Working docs (local only)

- Spec: `docs/superpowers/specs/2026-07-07-vanzelfsprekend-foundation-design.md`
- Plan: `docs/superpowers/plans/2026-07-07-vanzelfsprekend-foundation.md`
