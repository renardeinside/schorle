import Counter from "@/components/Counter";
import { getProps } from "@/lib/props";

export default async function Index() {
  const props = await getProps();
  return (
    <main className="min-h-screen grid place-items-center">
      <Counter />
    </main>
  );
}
