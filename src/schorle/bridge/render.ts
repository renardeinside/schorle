// renderer.ts — no top-level imports of react or react-dom/server!
import { createRequire } from "module";
import path from "path";
import { pathToFileURL } from "url";

export async function render(pageModulePath: string) {
  const abs = path.isAbsolute(pageModulePath)
    ? pageModulePath
    : path.join(process.cwd(), pageModulePath);

  const fileUrl = pathToFileURL(abs);
  const requireFromPage = createRequire(fileUrl);

  // Load the page module itself
  const { default: Page } = await import(fileUrl.href);

  // Load THE PAGE'S React + ReactDOM, not the CLI's
  const React = requireFromPage("react");
  const { renderToString } = requireFromPage("react-dom/server");

  const element = React.createElement(Page);
  return renderToString(element);
}
