gen-example:
    rm -rf examples/aurora && schorle init aurora examples/aurora

build-schorle:
    bun build.ts

render-to-std:
    cd examples/aurora && uv run python -c "from aurora.ui.generated import Index; print(Index.render())"

serve-in-aurora:
    cd examples/aurora && uv run uvicorn aurora.app:app --reload

gen-module:
    cd examples/aurora && uv run python -c "from schorle.generator import generate_module;from pathlib import Path; generate_module(Path('src/aurora/ui'))"