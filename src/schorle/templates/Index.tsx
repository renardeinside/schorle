import Counter from "@/components/Counter";
import { useProps, useHeaders, useCookies } from "@schorle/shared";
import { type StatsProps } from "@/lib/types";

export default function Index() {
  const props = useProps<StatsProps>();
  const headers = useHeaders();
  const cookies = useCookies();
  return (
    <main className="min-h-screen grid place-items-center">
      <Counter />
      <h2>Props</h2>
      <pre>
        <code>{JSON.stringify(props, null, 2)}</code>
      </pre>
      <h2>Headers</h2>
      <pre>
        <code>{JSON.stringify(headers, null, 2)}</code>
      </pre>
      <h2>Cookies</h2>
      <pre>
        <code>{JSON.stringify(cookies, null, 2)}</code>
      </pre>
    </main>
  );
}
