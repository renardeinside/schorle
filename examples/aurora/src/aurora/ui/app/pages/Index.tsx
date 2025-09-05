import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function Index() {
  const [count, setCount] = useState(0);
  return (
    <>
      <Button onClick={() => setCount(count + 1)}>Click me</Button>
      <div>Count: {count}</div>
    </>
  );
}
