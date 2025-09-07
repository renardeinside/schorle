"use client";

import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function Index() {
  const [count, setCount] = useState(0);
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <Button onClick={() => setCount(count + 1)}>Click me</Button>
      <div>Count: {count}</div>
    </div>
  );
}
