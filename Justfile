
stackenblochen:
    bunx prettier . --write
    uvx ruff format .

docs:
    cd docs && yarn dev

clean-aurora:
    mkdir -p packages/aurora
    rm -rf packages/aurora/*


install-shadcn-deps:
    bun add class-variance-authority clsx tailwind-merge lucide-react tw-animate-css

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