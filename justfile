# FRC Code Scout — site management tasks
#
# Targets:
#   just dev              — run the Hugo dev server with live reload
#   just build            — render D2 diagrams + build the Hugo site
#   just render-diagrams  — render D2 diagrams to SVG (run before just dev)
#   just clean            — remove generated artifacts

set shell := ["bash", "-euo", "pipefail", "-c"]

# Run the Hugo dev server with live reload
dev:
    hugo server --source site --buildDrafts --buildFuture --baseURL http://localhost:1313/

# Render D2 diagrams from docs/elite-arch/diagrams/ to SVG
render-diagrams:
    python3 scripts/render_diagrams.py

# Build the static site (diagrams + Hugo)
build: render-diagrams
    hugo --minify --source site

# Remove generated artifacts
clean:
    rm -rf site/public site/resources/_gen site/.hugo_build.lock site/static/diagrams