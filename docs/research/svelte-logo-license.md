# Svelte Logo: Sources & License (verified 2026-08-14)

## Verdict

Using the official Svelte logo on this site's marketing/landing pages is **allowed**. The
mark's usage conditions (see below) are satisfied by a starter kit that factually lists
"Svelte 5 islands" as part of its stack. No permission request is required.

## Official source

- **Branding repo:** https://github.com/sveltejs/branding (default branch: `master`)
  - `svelte-logo.svg` — classic S-shaped mark, orange `#ff3e00` (primary asset)
  - `svelte-logo-cutout.svg` — cutout version for overlays
  - `svelte-logo-square.svg` / `.png`, `svelte-horizontal.svg`, `svelte-vertical.svg`,
    `svelte-logotype.svg`, `svelte-logo.png`, `svelte-logo.pdf`
  - Direct file: `https://raw.githubusercontent.com/sveltejs/branding/master/svelte-logo.svg`
- **Primary repo:** https://github.com/sveltejs/svelte (MIT) — `LICENSE.md`:
  "Copyright (c) 2016-2025 Svelte Contributors ... Permission is hereby granted, free of
  charge, to any person obtaining a copy of this software and associated documentation
  files (the "Software"), to deal in the Software without restriction, including without
  limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
  and/or sell copies of the Software ..." (API license field: `MIT`, spdx `MIT`).
- **svelte.dev site repo:** https://github.com/sveltejs/svelte.dev — logo reused in
  several places (e.g. `apps/svelte.dev/content/tutorial/.../svelte-logo.svg`).

## Usage conditions (official branding README, quoted)

> 1. The term "Svelte logo" refers to the Svelte logo and other official artwork/mark.
>    It also includes the official color scheme used by the project.
> 3. Usage of the Svelte logo must not give the impression or implication that the Svelte
>    project (or any contributor to the project) is sponsoring or endorsing any other
>    project, service, product or organization.
> 4. Usage of the Svelte logo, to indicate, imply or assert compatibility or operability
>    with the Svelte library, must be accurate and done in good faith.

## Notes / caveats

- The `sveltejs/branding` repo itself has **no LICENSE file**; the logo files are also
  distributed inside the MIT-licensed `sveltejs/svelte` repo. The branding README's four
  conditions are the operative usage rules; no endorsement-implication is a condition, not
  the code license.
- MIT permits modification, so recolor/animate/extrude the SVG freely (e.g. GSAP/Three.js
  hero treatment). Keep the four conditions in mind: don't imply official endorsement and
  keep "compatible with Svelte" claims factual.
- No trademark registration was verified in this pass; treat "Svelte" as a protected mark
  and always pair the logo with accurate, non-endorsing context.

## Local copy

- Downloaded to `frontend/public/svelte-logo.svg` (official, unmodified, 1,892 bytes).
  Vite serves `public/` at `/static/` (base is `/static/`), so the URL is
  `/static/svelte-logo.svg`.
