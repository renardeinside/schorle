
fmt:
	hatch run lint:fmt .

test:
	hatch run test

test-cov:
	hatch run test-cov

lint:
	hatch run lint:style .

typing:
	hatch run lint:typing . --exclude=out

docs-deploy:
	@echo "Deploying docs infrastructure and the container..."
	cd docs/deployment && terraform apply --var-file=.tfvars
	@echo "Done."

docs-build:
	docker build --no-cache -t schorle-docs -f docs/Dockerfile.docs .

docs-serve: docs-build
	@echo "Serving docs..."
	docker run -p 4444:4444 -it schorle-docs
	@echo "Done."

docs-restart-app:
	@echo "Restarting docs app..."
	az webapp restart --name schorle-webapp --resource-group schorle-rg
	@echo "Done."

bundle-build:
	@echo "Building bundle..."
	yarn --cwd src/typescript build
	@echo "Done."

bundle-watch:
	@echo "Watching bundle..."
	yarn --cwd src/typescript watch