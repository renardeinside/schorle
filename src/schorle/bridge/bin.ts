#! /usr/bin/env bun
import { buildPages } from "./server/build";
import { render } from "./server/render";
import type { BuildProps, RenderProps } from "./server/types";

// All schorle commands must run in the project root
const projectRoot = process.cwd();

// app @-files are in $projectRoot/app
const appRoot = `${projectRoot}/app`;
// all pages are in $appRoot/pages
const pagesRoot = `${appRoot}/pages`;
// all schorle temp files are in $projectRoot/.schorle
const schorleRoot = `${projectRoot}/.schorle`;

async function main() {
  const [, , command, ...args] = process.argv;
  // two cmmands - build takes no arguments, render takes one argument
  if (!command || !["build", "render"].includes(command)) {
    console.error("Usage: schorle-bridge render|build");
    process.exit(1);
  }

  const buildProps: BuildProps = {
    projectRoot,
    appRoot,
    pagesRoot,
    schorleRoot,
  };

  if (command === "build") {
    await buildPages(buildProps);
  } else if (command === "render") {
    const pageName = args[0];
    if (!pageName) {
      console.error("Usage: schorle-bridge render <pageName>");
      process.exit(1);
    }
    const renderProps: RenderProps = { ...buildProps, pageName };
    await render(renderProps);
  } else {
    console.error("Usage: schorle-bridge <build|render>");
    process.exit(1);
  }
}

main();
