
stackenblochen:
    bunx prettier . --write
    uvx ruff check --fix .
    uvx ruff format .


fmt: stackenblochen

lint: 
    uvx ruff check .
    uv run mypy .

test:
    uv run pytest . --cov-report html

docs:
    cd docs && yarn dev

clean-aurora:
    mkdir -p packages/aurora
    rm -rf packages/aurora/*

[working-directory: 'packages/aurora']
init-aurora: clean-aurora
    bun init -y -m . && rm -rf ./.cursor

    uv init --name aurora --lib .
    uv run slx init src/aurora/ui
    uv run slx build

    cp ../../templates/app.py ./src/aurora/app.py
    cp ../../templates/models.py ./src/aurora/models.py
    cp ../../templates/api.py ./src/aurora/api.py
    cp ../../templates/About.mdx ./src/aurora/ui/pages/About.mdx

    uv run slx codegen aurora.models
    uv run slx generate-api-client aurora.app:app


[working-directory: 'packages/aurora']
in-aurora *args:
    {{args}}