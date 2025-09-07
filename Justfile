
stackenblochen:
    bunx prettier . --write
    uvx ruff format .

docs:
    cd docs && yarn dev

gen-project:
    rm -rf examples/aurora
    cd examples && uv init --no-workspace --package --name=aurora aurora
    cd examples/aurora && uv add ../../ --editable
    cd examples/aurora && uv run slx init aurora-ui src/aurora/ui
    cd examples/aurora && uv add uvicorn[standard]
    cd examples/aurora && cp ../../templates/app.py src/aurora/app.py

[working-directory: 'examples/aurora']
start-dev:
    uv run uvicorn aurora.app:app --reload

[working-directory: 'examples/aurora']
start-prod:
    uv run uvicorn aurora.app:app