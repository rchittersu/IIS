# Project page

Static page for GitHub Pages: `index.html` + `static/`. No build step.

**Host it:** push the repo, then on GitHub go to *Settings → Pages → Build and deployment*, choose *Deploy from a branch*, branch `main`, folder `/docs`. The page appears at `https://<user>.github.io/<repo>/`.

**Before publishing, replace the placeholders in `index.html`** (search for `TODO`):
- arXiv link: set to https://arxiv.org/abs/2511.15197
- `https://github.com/USERNAME/InsertInStyle` → code repository
- the "Benchmark soon" button → turn the `<span class="btn soon">` into `<a class="btn" href="GDRIVE_LINK">`

Preview locally: `python3 -m http.server -d docs 8000`, then open http://localhost:8000.
