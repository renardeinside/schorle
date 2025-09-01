gen-example:
    rm -rf examples/aurora && schorle init aurora examples/aurora

build-schorle:
    bun build.ts

run-in-aurora:
    uv --directory examples/aurora run python -c "from aurora.ui.app import app; print(app.root_path); print(app.dist_path);"

render-in-aurora:
    uv --directory examples/aurora run python -c "from aurora.ui.app import app; print(app.render('Index'))"

serve-in-aurora:
    cd examples/aurora && uv run uvicorn aurora.app:app --reload