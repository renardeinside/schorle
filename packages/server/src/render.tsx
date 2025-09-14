import { Console as NodeConsole } from "node:console";

// Send all SSR console output to *stderr* (stdout stays HTML-only)
const ssrConsole = new NodeConsole(process.stderr, process.stderr);
globalThis.console = ssrConsole as unknown as Console;

import { wrapLayouts } from "@schorle/shared";
import { renderToReadableStream } from "react-dom/server";
import { decode } from "msgpackr";
import { PropsProvider } from "@schorle/shared";

interface RenderInfo {
  page: string;
  layouts: string[];
  js: string;
}

export async function render(rawRenderInfo: string) {
  const renderInfo = JSON.parse(rawRenderInfo) as RenderInfo;

  // Read raw bytes once
  const stdinBuf = await new Response(Bun.stdin).arrayBuffer();
  const stdinU8 = new Uint8Array(stdinBuf);

  // 1) Use object for SSR
  const props = stdinU8.byteLength ? decode(stdinU8) : null;

  if (!renderInfo) {
    throw new Error("No render info provided");
  }

  const { page, layouts, js } = renderInfo;

  const Page = (await import(page)).default;
  const Layouts = await Promise.all(
    layouts.map((layout: string) => import(layout).then((mod) => mod.default)),
  );

  const pageTree = wrapLayouts(Page, Layouts);

  const element = <PropsProvider value={props}>{pageTree}</PropsProvider>;

  // prepares stream with JS injected, CSS is not there yet
  const reactStream = await renderToReadableStream(element, {
    bootstrapScripts: [js],
  });

  await reactStream.pipeTo(
    new WritableStream<Uint8Array>({
      write(chunk) {
        process.stdout.write(chunk);
      },
    }),
  );
}
