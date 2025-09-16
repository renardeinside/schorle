import { useProps } from "@schorle/shared";
import { type StatsProps } from "@/lib/types";

export default function Stats() {
  const props = useProps<StatsProps>();
  return (
    <div>
      Stats
      <p>Total users: {props.totalUsers}</p>
      <p>Last updated at: {props.lastUpdatedAt}</p>
    </div>
  );
}
