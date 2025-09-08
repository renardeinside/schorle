// lib/store.ts
import { headers } from "next/headers";
import { decode } from "@msgpack/msgpack";

// UDS configuration
const STORE_SOCKET_PATH = process.env.SCHORLE_STORE_SOCKET_PATH;

// TCP configuration
const STORE_HOST = process.env.SCHORLE_STORE_HOST;
const STORE_PORT = process.env.SCHORLE_STORE_PORT;

const getMode = () => {
  if (STORE_SOCKET_PATH) {
    return "uds";
  } else if (STORE_HOST && STORE_PORT) {
    return "http";
  } else {
    throw new Error(
      "Neither UDS (SCHORLE_STORE_SOCKET_PATH) nor TCP (SCHORLE_STORE_HOST/PORT) configuration found",
    );
  }
};

const fetchWithMode = async (schorleId: string) => {
  const mode = getMode();
  if (mode === "uds") {
    return fetch(`http://localhost/${schorleId}`, {
      unix: STORE_SOCKET_PATH,
    });
  } else if (mode === "http") {
    return fetch(`http://${STORE_HOST}:${STORE_PORT}/${schorleId}`);
  } else {
    throw new Error("Invalid mode");
  }
};

export async function getProps<T = unknown>(): Promise<T> {
  const schorleId = (await headers()).get("x-schorle-props-id");
  if (!schorleId) {
    throw new Error("No x-schorle-props-id header found");
  }

  const response = await fetchWithMode(schorleId);

  if (!response.ok) {
    throw new Error(
      `Failed to fetch props: ${response.status} ${response.statusText}`,
    );
  }

  const value = await response.arrayBuffer();
  return decode(value) as T;
}
