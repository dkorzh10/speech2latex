# Project-page live demo

`index.html` mounts the live microphone demo from the prebuilt `bundle.js`. Its
React source is in the [GitLab service](https://gitlab.2a2i.org/dev/speech2latex/-/tree/master/frontend),
so merging a frontend change there does not automatically update GitHub Pages.

The live Try selector includes only Math-1.5B and Qwen-0.5B equation checkpoints
(`equations` and `equations_05b`). Each model renders its full output as one formula.
The backend endpoint is recorded in `frontend-build.json` alongside the source
commit, local source patch and bundle checksum. No API secret belongs in this build.
The service API still supports sentence checkpoints; this selection is specific
to the GitHub Pages demo. Precomputed sentence examples remain available below.

To refresh the demo, use a clean service checkout at the `source_commit` recorded
in `frontend-build.json`. From the service repository root, apply this repository's
`docs/equations-only.patch` (replace `/path/to/speech2latex-gh` with its location):

```sh
git apply /path/to/speech2latex-gh/docs/equations-only.patch
cd frontend
npm ci
VITE_API_URL=https://speech2latex.axxx.tech npm run build
```

Copy `dist/assets/bundle.js` into this repository's `docs/bundle.js`. Update
`frontend-build.json` and the `bundle.js?v=...` URL in `index.html` using the first
12 characters of the new bundle's SHA-256. If styles or assets also change, sync
the corresponding CSS/assets and verify their deployment paths too.

The GitHub Pages workflow publishes `docs/` after changes are merged into the
upstream default branch. `demo_results.json` contains separate precomputed sample
outputs; updating the live demo bundle does not regenerate those results.
