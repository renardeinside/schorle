client-build:
	cd typescript && yarn build


client-watch:
	cd typescript && yarn watch

python-protogen:
	protoc -I=. --python_betterproto_out=src/schorle/proto_gen protobuf/*.proto

ts-protogen:
	protoc -I=. \
		--plugin=typescript/node_modules/.bin/protoc-gen-ts_proto \
		--ts_proto_out=typescript/proto_gen \
		--ts_proto_opt=oneof=unions \
		protobuf/*.proto

all-protogen: python-protogen ts-protogen
	@echo "Generated protobuf files"