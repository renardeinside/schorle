import type { BuildArtifact, BunPlugin } from "bun";
import plugin from "bun-plugin-tailwind";
import { relative } from "path";
import mdx from "@mdx-js/esbuild";

export async function build(hydratorPathsRaw: string) {
  if (!hydratorPathsRaw) {
    console.error("Please provide at least one entrypoint");
    process.exit(1);
  }

  if (hydratorPathsRaw.length === 0) {
    console.error("Please provide at least one entrypoint");
    process.exit(1);
  }

  const hydratorPaths = JSON.parse(hydratorPathsRaw) as string[];

  if (hydratorPaths.length === 0) {
    console.error("Please provide at least one entrypoint");
    process.exit(1);
  }

  const isDev = process.env.NODE_ENV !== "production";

  const entryName = isDev
    ? "pages/[dir]/[name]/dev.[ext]"
    : "pages/[dir]/[name]/[hash].[ext]";

  const chunkName = isDev
    ? "pages/[dir]/[name]/chunks/dev.[ext]"
    : "pages/[dir]/[name]/chunks/[hash].[ext]";
  const assetName = isDev
    ? "pages/[dir]/[name]/assets/dev.[ext]"
    : "pages/[dir]/[name]/assets/[hash].[ext]";

  const result = await Bun.build({
    entrypoints: hydratorPaths,
    outdir: ".schorle/dist/client",
    plugins: [
      plugin,
      mdx({
        jsxImportSource: "react",
        // This ensures MDX files are treated as JSX
        development: isDev,
      }) as unknown as BunPlugin,
    ],
    sourcemap: "inline",
    target: "browser",
    minify: true,
    // @ts-ignore
    splitting: true,
    naming: {
      entry: entryName,
      chunk: chunkName,
      asset: assetName,
    },
    define: {
      "process.env.NODE_ENV": JSON.stringify(
        isDev ? "development" : "production",
      ),
    },
  });

  if (result.success === false) {
    console.error("Build failed:", result.logs);
    process.exit(1);
  } else {
    const artifacts = result.outputs.map((o: BuildArtifact) => ({
      kind: o.kind, // "entry" | "chunk" | "asset"
      path: relative(".schorle/dist/client", o.path), // nice relative path
      loader: o.loader ?? null, // "js" | "css" | ...
      bytes: o.size ?? null, // size in bytes
    }));
    // Output the manifest payload to stdout for consumption by build.py
    // Use process.stdout.write() directly to ensure it goes to stdout, not stderr
    process.stdout.write(JSON.stringify(artifacts) + "\n");
  }
}
