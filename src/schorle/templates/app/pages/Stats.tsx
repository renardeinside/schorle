import { getSchorleProps } from "@/lib/props";

export default async function Stats() {
  const { total_users, last_updated_at } = await getSchorleProps<{
    total_users: number;
    last_updated_at: string;
  }>();

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-2xl font-bold">Stats</h1>
      <div>Total users: {total_users}</div>
      <div>Last updated at: {last_updated_at}</div>
    </div>
  );
}
