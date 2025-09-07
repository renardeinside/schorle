import net from "net";
import { headers } from "next/headers";

const SOCKET_PATH = process.env.SCHORLE_SOCKET_STORE_PATH;

if (!SOCKET_PATH) {
  throw new Error(
    "SCHORLE_SOCKET_STORE_PATH is not set. Make sure your Python app exports the store path to the Next.js process.",
  );
}

/**
 * The Python SocketStore server is single-request-per-connection:
 * - client sends: "GET /{key}\n"
 * - server replies with "value\n" then closes the connection
 *
 * We therefore open a new short-lived connection per request.
 * Additionally, we optionally keep a passive 'anchor' connection open
 * to keep the socket warm while the app is running.
 */
export class SocketStoreClient {
  private socketPath: string;

  constructor(socketPath: string) {
    this.socketPath = socketPath;
  }

  /**
   * Fetch a value for the given key. Resolves to empty string if missing.
   * Optional per-request timeout (ms).
   */
  get(key: string, timeoutMs = 1500): Promise<string> {
    return new Promise((resolve, reject) => {
      const client = net.createConnection(this.socketPath);
      let buf = "";
      let settled = false;

      const cleanup = () => {
        client.removeAllListeners();
        // End is triggered by server close anyway; ensure socket is gone
        try {
          client.end();
        } catch {
          /* noop */
        }
      };

      const timer =
        timeoutMs > 0
          ? setTimeout(() => {
              if (settled) return;
              settled = true;
              cleanup();
              reject(
                new Error(
                  `SocketStore get("${key}") timed out after ${timeoutMs}ms`,
                ),
              );
            }, timeoutMs)
          : undefined;

      client.on("connect", () => {
        client.write(`GET /${key}\n`);
      });

      client.on("data", (chunk) => {
        buf += chunk.toString("utf8");
      });

      client.on("end", () => {
        if (settled) return;
        settled = true;
        if (timer) clearTimeout(timer);
        cleanup();
        resolve(buf.replace(/\r?\n$/, "")); // strip trailing newline
      });

      client.on("error", (err) => {
        if (settled) return;
        settled = true;
        if (timer) clearTimeout(timer);
        cleanup();
        reject(err);
      });
    });
  }
}

// Singleton client used across the app
export const socketStoreClient = new SocketStoreClient(SOCKET_PATH);

export async function getSchorleProps<T = unknown>(): Promise<
  T | string | undefined
> {
  const headersList = await headers();
  const storeId = headersList.get("x-schorle-store-id");
  if (!storeId) {
    return undefined;
  }
  const raw = await socketStoreClient.get(storeId);
  if (!raw) return undefined;

  try {
    return JSON.parse(raw) as T;
  } catch {
    return raw; // not JSON; return as-is
  }
}
