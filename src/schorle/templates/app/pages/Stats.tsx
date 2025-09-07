"use client";
import { getSchorleProps } from "@/lib/store";

export default async function Stats() {
  const props = await getSchorleProps();
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <pre>
        <code>{JSON.stringify(props, null, 2)}</code>
      </pre>
    </div>
  );
}
