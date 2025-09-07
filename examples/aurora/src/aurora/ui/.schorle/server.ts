// custom server.ts for NextJS
// accepts incoming requests from UDS or TCP and forwards them to the NextJS server
// server.ts
import { parse } from "node:url";
import { createServer } from "node:http";
import next from "next";
import fs from "node:fs";

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

// Parse command line arguments
// Format: node server.ts <connection_mode> <connection_args...>
// UDS: node server.ts uds <socket_path> <store_socket_path>
// TCP: node server.ts tcp <host> <port> <store_host> <store_port>
const [, , connectionMode, ...connectionArgs] = process.argv;

if (!connectionMode || !connectionArgs.length) {
  console.error("Usage:");
  console.error("  UDS: node server.ts uds <socket_path> <store_socket_path>");
  console.error(
    "  HTTP: node server.ts http <host> <port> <store_host> <store_port>",
  );
  process.exit(1);
}

interface ConnectionConfig {
  mode: "uds" | "http";
  socketPath?: string;
  storeSocketPath?: string;
  host?: string;
  port?: number;
  storeHost?: string;
  storePort?: number;
}

let connectionConfig: ConnectionConfig = { mode: "uds" };

if (connectionMode === "uds") {
  const [socketPath, storeSocketPath] = connectionArgs;
  if (!socketPath || !storeSocketPath) {
    console.error("UDS mode requires socket_path and store_socket_path");
    process.exit(1);
  }
  connectionConfig = { mode: "uds", socketPath, storeSocketPath };
  process.env.SCHORLE_STORE_SOCKET_PATH = storeSocketPath;
} else if (connectionMode === "http") {
  const [host, port, storeHost, storePort] = connectionArgs;
  if (!host || !port || !storeHost || !storePort) {
    console.error("TCP mode requires host, port, store_host, store_port");
    process.exit(1);
  }
  connectionConfig = {
    mode: "http",
    host,
    port: parseInt(port),
    storeHost,
    storePort: parseInt(storePort),
  };
  process.env.SCHORLE_STORE_HOST = storeHost;
  process.env.SCHORLE_STORE_PORT = storePort;
} else {
  console.error(`Unknown connection mode: ${connectionMode}`);
  console.error("Supported modes: uds, http");
  process.exit(1);
}

await app.prepare();

const server = createServer((req, res) => {
  // Next expects Node's IncomingMessage/ServerResponse — which we already have here
  handle(req, res, parse(req.url!, true));
});

// Setup server listening based on connection mode
if (connectionConfig.mode === "uds") {
  const socketPath = connectionConfig.socketPath;
  if (!socketPath) {
    console.error("UDS mode requires socket_path");
    process.exit(1);
  }

  server.listen(socketPath, () => {
    // Set permissions if needed (e.g., for a reverse proxy user)
    console.log(`Next.js listening on unix://${socketPath}`);
  });
} else if (connectionConfig.mode === "http") {
  const { host, port } = connectionConfig;

  server.listen(port, host, () => {
    console.log(`Next.js listening on http://${host}:${port}`);
  });
}

// Graceful shutdown for UDS
for (const sig of ["SIGINT", "SIGTERM"] as const) {
  process.on(sig, () => {
    server.close(() => {
      process.exit(0);
    });
  });
}
