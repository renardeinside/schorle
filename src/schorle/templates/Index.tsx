import Counter from "@/components/Counter";
import { useProps } from "@schorle/shared";

export default function Index() {
  const props = useProps();
  return (
    <main className="min-h-screen grid place-items-center">
      <Counter />
      <h2>Props</h2>
      <pre>
        <code>{JSON.stringify(props, null, 2)}</code>
      </pre>
    </main>
  );
}
