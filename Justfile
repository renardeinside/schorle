gen-example:
    bun pm pack --destination .dev
    rm -rf examples/aurora
    uv init --package --name aurora examples/aurora --no-workspace
    uv --directory examples/aurora add fastapi uvicorn watchfiles
    uv --directory examples/aurora add --editable $(pwd)
    schorle init examples/aurora/src/aurora/ui
    cp templates/app.py examples/aurora/src/aurora/app.py

build-schorle:
    bun build.ts

render-to-std:
    cd examples/aurora && uv run python -c "from aurora.ui import Index; print(Index())"

serve-in-aurora:
    cd examples/aurora && uv run uvicorn aurora.app:app --reload \
        --reload-include '**/*.tsx' \
        --reload-exclude '**/temp/*.tsx' \
        --reload-exclude '**/ui/__init__.py'

gen-module:
    cd examples/aurora && uv run python -c "from schorle.generator import generate_module;from pathlib import Path; generate_module(Path('src/aurora/ui'))"

stackenblochen:
    bunx prettier . --write
    uvx ruff format .

docs:
    cd docs && yarn dev

build-from-shell:
    cd examples/aurora/src/aurora/ui && bun schorle-bridge build app/pages . .schorle/dist

render-from-shell:
    cd examples/aurora/src/aurora/ui && bun schorle-bridge render Index

render-from-python:
    cd examples/aurora && uv run schorle render src/aurora/ui Index