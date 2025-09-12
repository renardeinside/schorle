import { useState } from "react";
import { Button } from "@/components/ui/button";

export default function Index() {
  const [count, setCount] = useState(0);
  return (
    <main className="min-h-screen grid place-items-center">
      <div className="text-center">
        <div className="text-6xl font-semibold">{count}</div>
        <div className="mt-4 flex gap-2 justify-center">
          <Button onClick={() => setCount((c) => c - 1)}>-1</Button>
          <Button variant="secondary" onClick={() => setCount(0)}>
            Reset
          </Button>
          <Button onClick={() => setCount((c) => c + 1)}>+1</Button>
        </div>
      </div>
    </main>
  );
}
