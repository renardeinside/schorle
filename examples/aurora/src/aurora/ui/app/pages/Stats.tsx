import { getProps } from "@/lib/props";
import { StatsProps } from "@/lib/types";

export default async function Stats() {
  const { totalUsers, lastUpdatedAt } = await getProps<StatsProps>();

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-2xl font-bold">Stats</h1>
      <div>Total users: {totalUsers}</div>
      <div>Last updated at: {lastUpdatedAt}</div>
    </div>
  );
}
