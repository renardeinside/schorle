import plugin from "bun-plugin-tailwind";

export async function build(hydratorPathsRaw: string) {
  if (!hydratorPathsRaw) {
    console.error("Please provide at least one entrypoint");
    process.exit(1);
  }

  if (hydratorPathsRaw.length === 0) {
    console.error("Please provide at least one entrypoint");
    process.exit(1);
  }

  console.log("Building entry:", hydratorPathsRaw);

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
  });

  if (result.success === false) {
    console.error("Build failed:", result.logs);
    process.exit(1);
  } else {
    console.log("Build succeeded!");
  }
}
