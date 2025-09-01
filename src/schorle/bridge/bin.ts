#! /usr/bin/env bun
import { buildPages } from "./build";
import { render } from "./render";

async function main() {
  const [, , command, ...args] = process.argv;

  if (command === "build") {
    if (args.length !== 3) {
      console.error(
        "Usage: schorle-bridge build <sourceDir> <projectRoot> <outputDir>"
      );
      process.exit(1);
    }
    const sourceDir = args[0];
    const projectRoot = args[1];
    const outputDir = args[2];
    if (!sourceDir || !projectRoot || !outputDir) {
      console.error(
        "Usage: schorle-bridge build <sourceDir> <projectRoot> <outputDir>"
      );
      process.exit(1);
    }
    await buildPages({ sourceDir, projectRoot, outputDir });
  } else if (command === "render") {
    if (args.length !== 1) {
      console.error("Usage: schorle-bridge render <pageModulePath>");
      process.exit(1);
    }
    const pageModulePath = args[0];
    if (!pageModulePath || !pageModulePath.endsWith(".tsx")) {
      console.error("Usage: schorle-bridge render <pageModulePath>");
      process.exit(1);
    }
    const html = await render(pageModulePath);
    console.log(html);
  } else {
    console.error("Usage: schorle-bridge <build|render>");
    process.exit(1);
  }
}

main();
