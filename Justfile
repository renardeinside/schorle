
stackenblochen:
    bunx prettier . --write
    uvx ruff format .

docs:
    cd docs && yarn dev

gen-project:
    rm -rf examples/aurora
    cd examples && uv init --no-workspace --package --name=aurora aurora
    cd examples/aurora && uv add ../../ --editable
    cd examples/aurora && uv run slx init src/aurora/ui aurora-ui
    cd examples/aurora && uv add uvicorn[standard]
    cd examples/aurora && cp ../../templates/app.py src/aurora/app.py
    cd examples/aurora && cp ../../templates/models.py src/aurora/models.py
    cd examples/aurora && uv run slx codegen aurora.models


in-aurora *args:
    cd examples/aurora && {{args}}

in-aurora-ui *args:
    cd examples/aurora/src/aurora/ui/.schorle && {{args}}