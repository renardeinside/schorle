import { Console as NodeConsole } from "node:console";

// Send all SSR console output to *stderr* (stdout stays HTML-only)
const ssrConsole = new NodeConsole(process.stderr, process.stderr);
globalThis.console = ssrConsole as unknown as Console;

interface RenderRequest {
  props?: Uint8Array;
  headers?: Record<string, string> | null;
  cookies?: Record<string, string> | null;
  js: string;
  css?: string;
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
