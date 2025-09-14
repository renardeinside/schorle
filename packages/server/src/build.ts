import type { BuildArtifact } from "bun";
import plugin from "bun-plugin-tailwind";
import { relative } from "path";

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

  const result = await Bun.build({
    entrypoints: hydratorPaths,
    outdir: ".schorle/dist/entry",
    plugins: [plugin],
    sourcemap: "inline",
    target: "browser",
    minify: true,
    // @ts-ignore
    splitting: true,
    naming: {
      entry: "pages/[dir]/[name]/[hash].[ext]",
      chunk: "/chunks/[hash].[ext]",
      asset: "pages/[dir]/[name]/assets/[hash].[ext]",
    },
    define: { "process.env.NODE_ENV": JSON.stringify("development") },
  });

  if (result.success === false) {
    console.error("Build failed:", result.logs);
    process.exit(1);
  } else {
    const artifacts = result.outputs.map((o: BuildArtifact) => ({
      kind: o.kind, // "entry" | "chunk" | "asset"
      path: relative(".schorle/dist/entry", o.path), // nice relative path
      loader: o.loader ?? null, // "js" | "css" | ...
      bytes: o.size ?? null, // size in bytes
    }));
    Bun.write(
      ".schorle/dist/entry/manifest.json",
      JSON.stringify(artifacts, null, 2),
    );
  }
}
