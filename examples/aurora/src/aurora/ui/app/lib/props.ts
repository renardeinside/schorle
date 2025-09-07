// lib/store.ts
import { headers } from "next/headers";
import { decode } from "@msgpack/msgpack";

const STORE_SOCKET_PATH = process.env.SCHORLE_STORE_SOCKET_PATH;

export async function getSchorleProps<T = unknown>(): Promise<T> {
  const schorleId = (await headers()).get("x-schorle-props-id");
  if (!schorleId) {
    throw new Error("No x-schorle-props-id header found");
  }
  const response = await fetch(`http://localhost/${schorleId}`, {
    unix: STORE_SOCKET_PATH,
  });
  const value = await response.arrayBuffer();
  return decode(value) as T;
}
