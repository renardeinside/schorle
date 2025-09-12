import { wrapLayouts } from "@schorle/shared";
import { renderToReadableStream } from "react-dom/server";

interface RenderInfo {
  page: string;
  layouts: string[];
  js: string;
}

export async function render(rawRenderInfo: string) {
  const renderInfo = JSON.parse(rawRenderInfo) as RenderInfo;

  if (!renderInfo) {
    throw new Error("No render info provided");
  }

  const { page, layouts, js } = renderInfo;

  const Page = (await import(page)).default;
  const Layouts = await Promise.all(
    layouts.map((layout: string) => import(layout).then((mod) => mod.default)),
  );

  const element = wrapLayouts(Page, Layouts);

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
