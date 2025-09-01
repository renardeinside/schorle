import { rm } from "node:fs/promises";

console.log(`Building the schorle bridge...`);

// cleanup the dist directory
await rm("src/schorle/bin", { recursive: true, force: true });

await Bun.build({
  entrypoints: ["src/schorle/bridge/build.ts", "src/schorle/bridge/render.ts"],
  outdir: "src/schorle/bin",
  target: "bun",
  format: "esm",
  sourcemap: "none",
  minify: true,
  define: {
    "process.env.NODE_ENV": JSON.stringify(
      process.env.NODE_ENV || "development",
    ),
  },
  external: [],
});

console.log(`Bridge built successfully`);
