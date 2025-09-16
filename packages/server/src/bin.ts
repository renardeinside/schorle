#!/usr/bin/env bun

import { build } from "./build";
import { render, renderBuilt } from "./render";

const [, , command, ...args] = Bun.argv;

if (typeof Bun === "undefined") {
  throw new Error("@schorle/server requires Bun runtime");
}

if (command === "build") {
  const hydratorPathsRaw = args[0];
  if (!hydratorPathsRaw) {
    throw new Error("No hydrator paths provided");
  }
  await build(hydratorPathsRaw);
} else if (command === "render") {
  const renderInfo = args[0];
  if (!renderInfo) {
    throw new Error("No render info provided");
  }
  await render(renderInfo);
} else if (command === "render-built") {
  const serverJsPath = args[0];
  const renderRequest = args[1];
  if (!serverJsPath || !renderRequest) {
    throw new Error(
      "Server JS path and render request required for render-built",
    );
  }
  await renderBuilt(serverJsPath, renderRequest);
} else {
  throw new Error(`Unknown command ${command}`);
}
