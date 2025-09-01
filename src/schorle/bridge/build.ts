import plugin from "bun-plugin-tailwind";
import { join, relative, parse } from "path";
// Using node:fs for directory operations as recommended by Bun docs
// https://bun.com/docs/api/file-io#directories
import { readdir, stat, mkdir, rm } from "node:fs/promises";

// Re-export for convenience
export { plugin as tailwindPlugin };

interface BuildOptions {
  sourceDir: string;
  projectRoot: string;
  outputDir: string;
}

interface PageComponent {
  filePath: string;
  relativePath: string;
  componentName: string;
  outputName: string;
}

/**
 * Recursively scans a directory for .tsx files that contain default exports
 */
async function findTsxFiles(
  dir: string,
  baseDir: string,
): Promise<PageComponent[]> {
  const files: PageComponent[] = [];

  try {
    const entries = await readdir(dir);

    for (const entry of entries) {
      const fullPath = join(dir, entry);
      const stats = await stat(fullPath);

      if (stats.isDirectory()) {
        // Recursively scan subdirectories
        const subFiles = await findTsxFiles(fullPath, baseDir);
        files.push(...subFiles);
      } else if (entry.endsWith(".tsx")) {
        // filter out any file with __layout in the name
        if (entry.includes("__layout")) {
          continue;
        }
        // Check if file has default export by reading its content
        // Using Bun.file() for optimized file reading
        const fileContent = await Bun.file(fullPath).text();

        if (fileContent.includes("export default")) {
          const relativePath = relative(baseDir, fullPath);
          const parsed = parse(relativePath);
          const componentName = parsed.name;
          const outputName = relativePath
            .replace(/\.tsx$/, "")
            .replace(/[/\\]/g, "_");

          files.push({
            filePath: fullPath,
            relativePath,
            componentName,
            outputName,
          });
        }
      }
    }
  } catch (error) {
    console.error(`Error scanning directory ${dir}:`, error);
  }

  return files;
}

/**
 * Creates a client-side hydration entrypoint for a page component
 */
async function createHydrationEntrypoint(
  component: PageComponent,
  sourceDir: string,
): Promise<string> {
  // find the __layout.tsx file in the sourceDir
  const layoutFile = `${sourceDir}/__layout.tsx`;

  if (!Bun.file(layoutFile).exists()) {
    console.error(
      `No __layout.tsx file found in ${sourceDir} for ${component.componentName}`,
    );
    throw new Error(
      `No __layout.tsx file found in ${sourceDir} for ${component.componentName}`,
    );
  }

  // root path is always @/pages/__layout.tsx
  const rootLayoutPath = `@/pages/__layout.tsx`;
  const componentPath = `@/pages/${component.outputName}`;

  return `import React from 'react';
import { createRoot } from 'react-dom/client';
import Page from '${componentPath}';
import RootLayout from '${rootLayoutPath}';

// Client-side hydration
const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(React.createElement(RootLayout, null, React.createElement(Page)));
} else {
  console.error('Root element not found for hydration');
}
`;
}

/**
 * Main build function that processes page components and builds them with Bun
 *
 * @param options - Build configuration options
 * @param options.sourceDir - Directory recursively containing .tsx files with default exports
 * @param options.projectRoot - Directory with project root where package.json etc is defined
 * @param options.outputDir - Directory where compiled frontend should be saved
 *
 * @example
 * ```typescript
 * await buildPages({
 *   sourceDir: './src/ui/pages',
 *   projectRoot: process.cwd(),
 *   outputDir: './dist'
 * });
 * ```
 */
export async function buildPages(options: BuildOptions): Promise<void> {
  const { sourceDir, projectRoot, outputDir } = options;

  console.log("🔍 Scanning for page components...");

  // Find all .tsx files with default exports
  const pageComponents = await findTsxFiles(sourceDir, sourceDir);

  if (pageComponents.length === 0) {
    console.log("No page components found in", sourceDir);
    return;
  }

  console.log(`📦 Found ${pageComponents.length} page components:`);
  pageComponents.forEach((comp) => console.log(`  - ${comp.relativePath}`));

  // Create temporary directory for entrypoints
  const tempDir = join(projectRoot, ".schorle", "temp");
  await mkdir(tempDir, { recursive: true });

  try {
    // Create hydration entrypoints
    const entrypoints: Record<string, string> = {};

    for (const component of pageComponents) {
      // Calculate CSS path relative to temp directory
      const entrypointContent = await createHydrationEntrypoint(
        component,
        sourceDir,
      );
      const entrypointPath = join(tempDir, `${component.outputName}.tsx`);

      // Using Bun.write() for optimized file writing
      await Bun.write(entrypointPath, entrypointContent);
      entrypoints[component.outputName] = entrypointPath;
    }

    console.log("🚀 Building with Bun...");

    // Ensure output directory exists
    await mkdir(outputDir, { recursive: true });

    // Build all entrypoints using Bun's build API
    const result = await Bun.build({
      entrypoints: Object.values(entrypoints),
      outdir: outputDir,
      plugins: [plugin],
      sourcemap: "linked",
      minify: true,
      naming: "[name].[ext]", // Ensure flat naming without hash for predictable filenames
      root: tempDir, // Use temp dir as root to avoid nested structure
      // Configure external modules that should not be bundled
      external: [],
      // Target modern browsers
      target: "browser",
      format: "esm",
    });

    if (result.success) {
      console.log("✅ Build completed successfully!");
      console.log(`📁 Output directory: ${outputDir}`);
      console.log(`🗂️  Generated ${result.outputs.length} output files:`);

      // Log output files
      result.outputs.forEach((output) => {
        const relativePath = relative(outputDir, output.path);
        console.log(
          `  - ${output.path} (${(output.size / 1024).toFixed(2)} KB)`,
        );
      });

      // Create a manifest file mapping original components to built outputs
      const manifest: Record<string, { js: string; css?: string }> = {};

      for (const [name, path] of Object.entries(entrypoints)) {
        const jsFile = result.outputs.find(
          (out) => out.path.includes(name) && out.path.endsWith(".js"),
        );
        const cssFile = result.outputs.find(
          (out) => out.path.includes(name) && out.path.endsWith(".css"),
        );

        if (jsFile) {
          const entry: { js: string; css?: string } = {
            js: relative(outputDir, jsFile.path),
          };

          if (cssFile) {
            entry.css = relative(outputDir, cssFile.path);
          }

          manifest[name] = entry;
        }
      }

      const manifestPath = join(outputDir, "manifest.json");
      // Using Bun.write() for optimized JSON file writing
      await Bun.write(manifestPath, JSON.stringify(manifest, null, 2));
      console.log(
        `📋 Created manifest at: ${relative(projectRoot, manifestPath)}`,
      );
    } else {
      console.error("❌ Build failed:");
      result.logs.forEach((log) => console.error(log));
      throw new Error("Build process failed");
    }
  } finally {
    // Clean up temporary files
    try {
      await rm(tempDir, { recursive: true, force: true });
    } catch (error) {
      console.warn("Failed to clean up temporary directory:", error);
    }
  }
}

export default buildPages;
