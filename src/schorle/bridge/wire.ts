import { build as viteBuild } from "vite";
import * as path from "jsr:@std/path";
import { renderToString } from "react-dom/server";
import React from "react";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// --- Utilities ---
async function listPages(pagesDir: string): Promise<string[]> {
  console.log("📄 Listing pages in:", pagesDir);
  const pages: string[] = [];
  for await (const dirEntry of Deno.readDir(pagesDir)) {
    if (dirEntry.isFile && dirEntry.name.endsWith(".tsx")) {
      pages.push(path.join(pagesDir, dirEntry.name));
    }
  }
  console.log(`🔍 Found ${pages.length} page(s):`, pages);
  return pages;
}

const getHydratorCode = (pageImportPath: string) => `
import { hydrateRoot } from "react-dom/client";
import * as page from "${pageImportPath}";
import { Layout } from "@/layouts/default.tsx";
import "@/index.css";

hydrateRoot(
  document.getElementById("root")!,
  <Layout><page.default /></Layout>
);
`;

// --- Build SSR Modules ---
async function buildSSR(frontendPath: string, pages: string[]) {
  console.log("⚙️  Starting SSR build...");
  const ssrOutDir = path.join("__dist", "ssr");

  await viteBuild({
    plugins: [react(), tailwindcss()],
    mode: "production",
    root: frontendPath,
    resolve: {
      alias: {
        "@/": path.join(frontendPath, "/"),
      },
    },
    build: {
      ssr: true,
      outDir: ssrOutDir,
      manifest: true,
      emptyOutDir: true,
      minify: false,
      rollupOptions: {
        input: pages,
      },
    },
    define: {
      "process.env.NODE_ENV": JSON.stringify("development"),
    },
  });

  console.log("✅ SSR code built to", ssrOutDir);
}

// --- Build Client Hydrators ---
async function buildClient(frontendPath: string, pages: string[]) {
  console.log("⚙️  Starting client build...");

  const distDir = "__dist";
  const tempDir = path.join(frontendPath, distDir, "temp");
  const clientOutDir = path.join(distDir, "client");

  // Create temp directory
  await Deno.mkdir(tempDir, { recursive: true });
  console.log("🗂️  Temp directory created at:", tempDir);

  const hydrators = new Map<string, string>();

  for (const page of pages) {
    const pageName = path.basename(page, ".tsx");
    const hydratorPath = path.join(tempDir, `${pageName}.tsx`);
    const aliasedPath = `@/pages/${pageName}.tsx`;
    const code = getHydratorCode(aliasedPath);
    console.log(`Hydrator code for ${pageName}:\n`, code);

    await Deno.writeTextFile(hydratorPath, code);
    hydrators.set(pageName, hydratorPath);
    console.log(`🧩 Hydrator created for page: ${pageName}`);
  }

  const rollupInputs = Object.fromEntries(hydrators.entries());

  console.log("📦 Rollup inputs for client build:", rollupInputs);

  await viteBuild({
    plugins: [react(), tailwindcss()],
    mode: "production",
    root: frontendPath,
    resolve: {
      alias: {
        "@/": path.join(frontendPath, "/"),
      },
    },
    build: {
      outDir: clientOutDir,
      manifest: true,
      emptyOutDir: true,
      minify: false,
      rollupOptions: {
        input: rollupInputs,
      },
    },
    define: {
      "process.env.NODE_ENV": JSON.stringify("development"),
    },
  });

  console.log("✅ Client code built to", clientOutDir);
}

// --- Main Entrypoint ---
export async function build(frontendPath: string) {
  console.log("🚀 Build process started for:", frontendPath);
  const pagesDir = path.join(frontendPath, "pages");
  const pages = await listPages(pagesDir);

  // cleanup dist directory
  Deno.remove(path.join(frontendPath, "__dist"), { recursive: true }).catch(
    () => {}
  );

  console.log("🏗️  Building SSR...");
  await buildSSR(frontendPath, pages);

  console.log("🏗️  Building client bundles...");
  await buildClient(frontendPath, pages);

  console.log("🎉 Full build complete.");
}

// --- Render Function (for SSR) ---
export async function render(pageModulePath: string) {
  const { default: Page } = await import(pageModulePath);
  const { Layout } = await import("@/layouts/default.tsx");
  const html = renderToString(
    React.createElement(Layout, null, React.createElement(Page))
  );
  return html;
}

if (import.meta.main) {
  const [cmd, frontendPath] = Deno.args;
  if (cmd === "build") {
    await build(frontendPath);
  }
  if (cmd === "render") {
    const [pageModulePath] = Deno.args.slice(1);
    const html = await render(pageModulePath);
    console.log(html);
  }
  Deno.exit(0);
}
