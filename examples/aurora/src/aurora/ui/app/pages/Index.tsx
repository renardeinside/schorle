import { Button } from "@/components/ui/button";
import { Suspense, useState } from "react";

// --- tiny helper the server can await ---
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * This async component runs during SSR.
 * Because it awaits, it will SUSPEND on the server and stream in later.
 * Wrapped in <Suspense>, you'll first see the fallback, then this content
 * pops in WITHOUT blocking hydration of the rest of the page.
 */
async function SlowServerSection() {
  // Simulate server work (DB call, FS, fetch, etc.)
  await sleep(1500);
  const now = new Date().toLocaleTimeString();
  return (
    <div className="mt-6 rounded-xl border p-4">
      <div className="font-medium">Server-chunk arrived ✅</div>
      <div className="text-sm text-muted-foreground">Rendered at: {now}</div>
    </div>
  );
}

/**
 * Another async server piece to make the effect obvious:
 * renders a small list after ~2.5s.
 */
async function SlowServerList() {
  await sleep(2500);
  const items = ["Alpha", "Bravo", "Charlie"];
  return (
    <ul className="mt-3 list-disc pl-6">
      {items.map((x) => (
        <li key={x}>{x}</li>
      ))}
    </ul>
  );
}

const Counter = () => {
  const [count, setCount] = useState(0);
  return (
    <div>
      <Button onClick={() => setCount((c) => c + 1)}>Click me</Button>
      <div>Count: {count}</div>
    </div>
  );
}
export default function Index() {

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-6">
      {/* Client interactivity hydrates immediately */}
      <div className="flex items-center gap-4">
        <Counter />
      </div>

      {/* Suspense boundary #1: streams when SlowServerSection resolves */}
      <Suspense
        fallback={
          <div className="mt-6 w-[28rem] animate-pulse rounded-xl border p-4">
            <div className="h-4 w-40 rounded bg-muted/60" />
            <div className="mt-2 h-3 w-64 rounded bg-muted/50" />
          </div>
        }
      >
        <SlowServerSection />
      </Suspense>

      {/* Suspense boundary #2: independent stream */}
      <Suspense
        fallback={
          <div className="w-[28rem] animate-pulse rounded-xl border p-4">
            <div className="h-4 w-28 rounded bg-muted/60" />
            <div className="mt-2 h-3 w-48 rounded bg-muted/50" />
            <div className="mt-2 h-3 w-56 rounded bg-muted/50" />
          </div>
        }
      >
        <SlowServerList />
      </Suspense>
    </div>
  );
}
