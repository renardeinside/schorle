import type { BuildArtifact, BunPlugin } from "bun";
import plugin from "bun-plugin-tailwind";
import { relative } from "path";
import mdx from "@mdx-js/esbuild";

interface BuildConfig {
  client?: string[];
  server?: string[];
}

export async function build(configRaw: string) {
  if (!configRaw) {
    console.error("Please provide build configuration");
    process.exit(1);
  }

  if (configRaw.length === 0) {
    console.error("Please provide build configuration");
    process.exit(1);
  }

  const config = JSON.parse(configRaw) as BuildConfig;

  // Support legacy format (just array of client paths)
  const legacyPaths = Array.isArray(JSON.parse(configRaw))
    ? (JSON.parse(configRaw) as string[])
    : null;
  if (legacyPaths) {
    config.client = legacyPaths;
  }

  if (
    (!config.client || config.client.length === 0) &&
    (!config.server || config.server.length === 0)
  ) {
    console.error("Please provide at least one client or server entrypoint");
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

  const allArtifacts: any[] = [];

  // Build client entries if they exist
  if (config.client && config.client.length > 0) {
    const clientResult = await Bun.build({
      entrypoints: config.client,
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

    if (clientResult.success === false) {
      console.error("Client build failed:", clientResult.logs);
      process.exit(1);
    } else {
      const clientArtifacts = clientResult.outputs.map((o: BuildArtifact) => ({
        kind: o.kind, // "entry" | "chunk" | "asset"
        path: relative(".schorle/dist/client", o.path), // nice relative path
        loader: o.loader ?? null, // "js" | "css" | ...
        bytes: o.size ?? null, // size in bytes
        target: "client", // identify as client artifact
      }));
      allArtifacts.push(...clientArtifacts);
    }
  }

  // Build server entries if they exist
  if (config.server && config.server.length > 0) {
    const serverResult = await Bun.build({
      entrypoints: config.server,
      outdir: ".schorle/dist/server",
      plugins: [
        mdx({
          jsxImportSource: "react",
          development: isDev,
        }) as unknown as BunPlugin,
      ],
      sourcemap: "inline",
      target: "node",
      minify: false, // Keep readable for server-side debugging
      splitting: false, // No splitting for server bundles
      naming: {
        entry: entryName,
      },
      define: {
        "process.env.NODE_ENV": JSON.stringify(
          isDev ? "development" : "production",
        ),
      },
      external: ["react", "react-dom", "@schorle/shared", "msgpackr"],
    });

    if (serverResult.success === false) {
      console.error("Server build failed:", serverResult.logs);
      process.exit(1);
    } else {
      const serverArtifacts = serverResult.outputs.map((o: BuildArtifact) => ({
        kind: o.kind, // "entry" | "chunk" | "asset"
        path: relative(".schorle/dist/server", o.path), // nice relative path
        loader: o.loader ?? null, // "js" | "css" | ...
        bytes: o.size ?? null, // size in bytes
        target: "server", // identify as server artifact
      }));
      allArtifacts.push(...serverArtifacts);
    }
  }

  // Output the manifest payload to stdout for consumption by build.py
  // Use process.stdout.write() directly to ensure it goes to stdout, not stderr
  process.stdout.write(JSON.stringify(allArtifacts) + "\n");
}
