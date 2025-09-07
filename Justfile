
stackenblochen:
    bunx prettier . --write
    uvx ruff format .

docs:
    cd docs && yarn dev

[working-directory: 'examples/slx-ex']
gen-registry:
    uv run schorle registry app/pages .schorle/app/registry.gen.tsx registry.py

[working-directory: 'examples/slx-ex']
start:
    uv run uvicorn main:app --reload