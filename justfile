# FRC Code Scout — site management tasks
#
# Targets:
#   just dev       — run the Hugo dev server with live reload
#   just build     — build the Hugo site into site/public
#   just clean     — remove generated Hugo artifacts

set shell := ["bash", "-euo", "pipefail", "-c"]

# Run the Hugo dev server with live reload
dev:
    hugo server --source site --buildDrafts --buildFuture --baseURL http://localhost:1313/

# Build the static site
build:
    hugo --minify --source site

# Remove generated Hugo artifacts
clean:
    rm -rf site/public site/resources/_gen site/.hugo_build.lock
