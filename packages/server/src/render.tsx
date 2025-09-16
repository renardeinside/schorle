import { Console as NodeConsole } from "node:console";

// Send all SSR console output to *stderr* (stdout stays HTML-only)
const ssrConsole = new NodeConsole(process.stderr, process.stderr);
globalThis.console = ssrConsole as unknown as Console;

// Configure MDX handling for server-side rendering
import { plugin } from "bun";
import mdx from "@mdx-js/esbuild";

plugin(
  mdx({
    jsxImportSource: "react",
    development: process.env.NODE_ENV !== "production",
  }) as any,
);

import { wrapLayouts } from "@schorle/shared";
import { renderToReadableStream } from "react-dom/server";
import { decode } from "msgpackr";
import { PropsProvider } from "@schorle/shared";

interface RenderInfo {
  page: string;
  layouts: string[];
  js: string;
  css: string;
  headers?: Record<string, string> | null;
  cookies?: Record<string, string> | null;
}

interface RenderRequest {
  props?: Uint8Array;
  headers?: Record<string, string> | null;
  cookies?: Record<string, string> | null;
  js: string;
  css?: string;
}

// Legacy render function for backward compatibility
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

  const { page, layouts, js, headers, cookies } = renderInfo;

  // Set headers and cookies on global objects for SSR hooks
  if (headers) {
    (globalThis as any).__SCHORLE_HEADERS__ = headers;
  }
  if (cookies) {
    (globalThis as any).__SCHORLE_COOKIES__ = cookies;
  }

  const Page = (await import(page)).default;
  const Layouts = await Promise.all(
    layouts.map((layout: string) => import(layout).then((mod) => mod.default)),
  );

  const pageTree = wrapLayouts(Page, Layouts);

  const element = <PropsProvider value={props}>{pageTree}</PropsProvider>;

  // prepares stream with JS injected, CSS is not there yet
  const reactStream = await renderToReadableStream(element, {
    bootstrapModules: [js],
  });

  await reactStream.pipeTo(
    new WritableStream<Uint8Array>({
      write(chunk) {
        process.stdout.write(chunk);
      },
    }),
  );
}

// New render function for built server modules
export async function renderBuilt(
  serverJsPath: string,
  rawRenderRequest: string,
) {
  // Read raw bytes from stdin (props)
  const stdinBuf = await new Response(Bun.stdin).arrayBuffer();
  const stdinU8 = new Uint8Array(stdinBuf);

  const renderRequest = JSON.parse(rawRenderRequest) as RenderRequest;

  // Import the built server module
  const serverModule = await import(serverJsPath);

  if (!serverModule.render || typeof serverModule.render !== "function") {
    throw new Error(
      `Built server module does not export a render function: ${serverJsPath}`,
    );
  }

  // Prepare the render request with actual props bytes
  const request: RenderRequest = {
    ...renderRequest,
    props: stdinU8.byteLength ? stdinU8 : undefined,
  };

  // Call the render function from the built module
  const reactStream = await serverModule.render(request);

  // Pipe the stream to stdout
  await reactStream.pipeTo(
    new WritableStream<Uint8Array>({
      write(chunk) {
        process.stdout.write(chunk);
      },
    }),
  );
}
