# Project page

Static page for GitHub Pages: `index.html` + `static/`. No build step.

**Live at:** https://rchittersu.github.io/IIS/ (served from branch `main`, folder `/docs`; it redeploys a minute or two after each push).

**Still to do:** once the checkpoint is uploaded, turn the "Checkpoint soon" button in `index.html` (the `<span class="btn soon">`) into `<a class="btn" href="GDRIVE_LINK">`, and add the same link in the top-level `README.md`.

Preview locally: `python3 -m http.server -d docs 8000`, then open http://localhost:8000.
