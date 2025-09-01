// renderer.ts — no top-level imports of react or react-dom/server!
import { createRequire } from "module";
import path from "path";
import { pathToFileURL } from "url";

export async function render(pageModulePath: string) {
  const abs = path.isAbsolute(pageModulePath)
    ? pageModulePath
    : path.join(process.cwd(), pageModulePath);
  // find the __layout.tsx file in the same directory as the page module path
  const rootFile = `${path.dirname(pageModulePath)}/__layout.tsx`;
  if (!Bun.file(rootFile).exists()) {
    throw new Error(
      `No __layout.tsx file found in ${path.dirname(pageModulePath)}`,
    );
  }

  const fileUrl = pathToFileURL(abs);
  const requireFromPage = createRequire(fileUrl);

  // Load the page module itself
  const { default: Page } = await import(fileUrl.href);

  // Load the root layout module itself
  const { default: RootLayout } = await import(pathToFileURL(rootFile).href);

  // Load THE PAGE'S React + ReactDOM, not the CLI's
  const React = requireFromPage("react");
  const { renderToString } = requireFromPage("react-dom/server");

  const element = React.createElement(
    RootLayout,
    null,
    React.createElement(Page),
  );
  return renderToString(element);
}
