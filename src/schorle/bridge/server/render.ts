import path from "path";
import { renderToReadableStream } from "react-dom/server";
import { findLayouts, type PageComponent } from "./build";
import { wrapLayouts } from "../shared";
import type { Manifest, RenderProps } from "./types";

export async function render(props: RenderProps) {
  const pageModulePath = path.join(props.pagesRoot, `${props.pageName}.tsx`);

  const pageComponent = {
    pageName: props.pageName,
    pagePath: pageModulePath,
    pageDir: path.dirname(pageModulePath),
  } satisfies PageComponent;

  const replaceable = `${props.projectRoot}/app`;
  const replacementTarget = `@`;

  const layoutPaths = (await findLayouts(pageComponent, props.projectRoot)).map(
    (path) => path.replace(replaceable, replacementTarget),
  );
  const layouts = await Promise.all(
    layoutPaths.map(async (path) => {
      return (await import(path)).default;
    }),
  );

  const { default: Page } = await import(
    pageComponent.pagePath.replace(replaceable, replacementTarget)
  );

  const pageManifest = (await Bun.file(
    path.join(
      props.schorleRoot,
      "dist",
      "pages",
      props.pageName,
      "manifest.json",
    ),
  ).json()) as Manifest;

  const element = wrapLayouts(Page, layouts);

  // prepares stream with JS injected, CSS is not there yet
  const reactStream = await renderToReadableStream(element, {
    bootstrapScripts: [`/${pageManifest.js}`],
  });

  // inject CSS
  const transform = new TransformStream({
    async transform(chunk, controller) {
      const text = new TextDecoder().decode(chunk);
      if (text.includes("</head>")) {
        const insertions = `
          <script>
            window.__SCHORLE_HYDRATION_PROPS__ = ${JSON.stringify({
              pagePath: pageComponent.pagePath,
              layoutPaths: layoutPaths,
            })}
          </script>
          <link rel="preload" href="/${pageManifest.css}" as="style">
          <link rel="stylesheet" href="/${pageManifest.css}">
          <script>
            (function(){try{var t=localStorage.getItem('theme');
            if(!t)t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
            document.documentElement.classList.toggle('dark', t==='dark');}catch(e){}})();
          </script>
          `;
        const patched = text.replace("</head>", `${insertions}</head>`);
        controller.enqueue(new TextEncoder().encode(patched));
      } else {
        controller.enqueue(chunk);
      }
    },
  });

  await reactStream.pipeThrough(transform).pipeTo(
    new WritableStream<Uint8Array>({
      write(chunk) {
        process.stdout.write(chunk);
      },
    }),
  );
}
