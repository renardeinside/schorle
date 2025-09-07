// custom server.ts for NextJS
// accepts incoming requests from a UDP socket and forwards them to the NextJS server
// server.ts
import { parse } from "node:url";
import { createServer } from "node:http";
import next from "next";
import fs from "node:fs";

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

const [, , SOCKET_PATH, STORE_SOCKET_PATH] = process.argv;

if (!SOCKET_PATH || !STORE_SOCKET_PATH) {
  console.error("Usage: node server.ts <socket_path> <store_socket_path>");
  process.exit(1);
}

process.env.SCHORLE_SOCKET_STORE_PATH = STORE_SOCKET_PATH;

await app.prepare();

// Clean up stale socket (helps during restarts)
try {
  if (fs.existsSync(SOCKET_PATH)) fs.unlinkSync(SOCKET_PATH);
} catch (e) {
  console.warn("Could not remove stale socket:", e);
}

const server = createServer((req, res) => {
  // Next expects Node's IncomingMessage/ServerResponse — which we already have here
  handle(req, res, parse(req.url!, true));
});

server.listen(SOCKET_PATH, () => {
  // Set permissions if needed (e.g., for a reverse proxy user)
  try {
    fs.chmodSync(SOCKET_PATH, 0o777);
  } catch {}
  console.log(`Next.js listening on unix://${SOCKET_PATH}`);
});

// Graceful shutdown
for (const sig of ["SIGINT", "SIGTERM"] as const) {
  process.on(sig, () => {
    server.close(() => {
      try {
        if (fs.existsSync(SOCKET_PATH)) fs.unlinkSync(SOCKET_PATH);
      } catch {}
      process.exit(0);
    });
  });
}
