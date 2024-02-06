HTMX_VERSION=1.9.10
IDIOMORPH_VERSION=0.3.0
HTMX_DEPS_DIR=src/schorle/assets/dependencies

download-htmx-dev-deps:
	rm -rf $(HTMX_DEPS_DIR)
	mkdir -p $(HTMX_DEPS_DIR)
	cd $(HTMX_DEPS_DIR) && wget https://raw.githubusercontent.com/bigskysoftware/htmx/v$(HTMX_VERSION)/src/htmx.js
	cd $(HTMX_DEPS_DIR) && wget https://raw.githubusercontent.com/bigskysoftware/htmx/v$(HTMX_VERSION)/src/ext/ws.js
	cd $(HTMX_DEPS_DIR) && wget https://raw.githubusercontent.com/bigskysoftware/idiomorph/v$(IDIOMORPH_VERSION)/src/idiomorph-htmx.js
	cd $(HTMX_DEPS_DIR) && wget https://raw.githubusercontent.com/bigskysoftware/idiomorph/v$(IDIOMORPH_VERSION)/src/idiomorph.js


deploy-docs:
	@echo "Deploying docs page..."
	cd docs/deployment && terraform apply -auto-approve --var-file=.tfvars