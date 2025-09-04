// build.ts
import plugin from "bun-plugin-tailwind";
import { join, relative } from "path";
import { readdir, stat, mkdir, rm } from "node:fs/promises";
import React from "react";
import path from "path";
import { encodeHydrationProps } from "../shared/hydrationProps";
import type { BuildProps } from "./types";

export { plugin as tailwindPlugin };

export interface PageComponent {
  pageName: string; // page name without extension, e.g. "Index"
  pagePath: string; // relative to the project root path to the page (incl. filename), e.g. "pages/Index.tsx", or "pages/subfolder/Index.tsx"
  pageDir: string; // relative to the project root path to the page directory, e.g. "pages", or "pages/subfolder"
}

export async function findLayouts(
  pageComponent: PageComponent,
  projectRoot: string,
): Promise<string[]> {
  // folder structure is:
  // projectRoot/app/pages/subfolder/Index.tsx
  // projectRoot/app/pages/subfolder/__layout.tsx
  // so we need to go through each folder in the page path upwards until we reach the projectRoot, and find all __layout.tsx files
  const layoutPaths: string[] = [];
  let currentDir = pageComponent.pageDir;
  while (currentDir !== projectRoot) {
    const layout = join(currentDir, "__layout.tsx");
    if (await Bun.file(layout).exists()) {
      layoutPaths.push(layout);
    }
    currentDir = path.dirname(currentDir);
  }
  return layoutPaths;
}

async function findPages(pagesRoot: string): Promise<PageComponent[]> {
  const out: PageComponent[] = [];
  const entries = await readdir(pagesRoot);
  for (const name of entries) {
    const p = join(pagesRoot, name);
    const st = await stat(p);
    if (st.isDirectory()) {
      out.push(...(await findPages(p)));
    } else if (name.endsWith(".tsx") && !name.includes("__layout")) {
      const text = await Bun.file(p).text();
      if (text.includes("export default")) {
        out.push({
          pageName: name.replace(/\.tsx$/, ""),
          pagePath: p,
          pageDir: path.dirname(p),
        });
      }
    }
  }
  return out;
}

export async function buildPages(props: BuildProps): Promise<void> {
  // print information about the React version and path of the React package
  console.log("🔍 React version:", React.version);

  console.log("🔍 Scanning for pages…");
  const pages = await findPages(props.pagesRoot);
  if (pages.length === 0) {
    console.log("ℹ️ No pages found in", props.pagesRoot);
    return;
  }
  pages.forEach((p) => console.log(`  📄 ${p.pageName} at ${p.pagePath}`));

  // prepare typescript registry of all pages AND layouts

  console.log(`🔍 Scanning for files in ${props.pagesRoot}`);
  const fileGlob = new Bun.Glob(`**/*.tsx`);
  const found = await Array.fromAsync(fileGlob.scan(`${props.pagesRoot}`));

  console.log(`🔍 Found ${found.length} files`);

  let lines = found.map((n) => {
    const key = n.replace(/\.(t|j)sx?$/, "");
    // get path in format @/pages/subfolder/Index.tsx
    const spec = `@/pages/${n}`;
    return `  "${key}": () => import("${spec}")`;
  });
  lines = lines.filter((n) => n !== null);

  const out = `export const registry = {\n${lines.join(",\n")}\n} as const;\n`;
  Bun.write(`${props.appRoot}/registry.ts`, out);
  console.log(`Wrote ${props.appRoot}/registry.ts`);

  pages.forEach(async (p) => {
    const layouts = await findLayouts(p, props.projectRoot);

    const hydratorPath = new URL(
      import.meta.resolve("@schorle/bridge/hydrator"),
    ).pathname;

    const pageOutputDir = `${props.schorleRoot}/dist/pages/${p.pageName}`;

    // remove the directory if it exists
    if (await Bun.file(pageOutputDir).exists()) {
      await rm(pageOutputDir, { recursive: true, force: true });
    }
    await mkdir(pageOutputDir, { recursive: true });

    const output = await Bun.build({
      entrypoints: [hydratorPath],
      outdir: pageOutputDir,
      plugins: [plugin],
      sourcemap: "inline",
      target: "browser",
      minify: true,
      // @ts-ignore
      splitting: false,
      naming: {
        entry: "[dir]/[name]-[hash].[ext]",
        chunk: "chunks/[name]-[hash].[ext]",
        asset: "assets/[name]-[hash].[ext]",
      },
      define: {
        "window.__SCHORLE_HYDRATION_PROPS__": encodeHydrationProps({
          pagePath: p.pagePath,
          layoutPaths: layouts,
        }),
      },
    });
    if (output.success) {
      // write the manifest to the pageDir
      const js = output.outputs?.[0]?.path;
      const css = output.outputs?.[1]?.path;
      if (!js || !css) {
        throw new Error(`Failed to build ${p.pageName} at ${p.pagePath}`);
      }
      // make paths relative to project root
      const jsPath = relative(props.projectRoot, js);
      const cssPath = relative(props.projectRoot, css);
      const manifest = {
        js: jsPath,
        css: cssPath,
      };
      await Bun.write(
        join(props.schorleRoot, "dist", "pages", p.pageName, "manifest.json"),
        JSON.stringify(manifest, null, 2),
      );
      console.log(`  ✅ ${p.pageName} at ${p.pagePath} built successfully`);
    } else {
      console.error(`  ❌ ${p.pageName} at ${p.pagePath} built failed`);
      console.error(output.logs);
    }
  });
}

export default buildPages;
