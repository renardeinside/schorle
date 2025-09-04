// defines SerDE logic for defining hydration props

// Bun.build receives {define: Record<string, string>}, so encoding is needed
// Window receives everything as strings, so decoding is needed

export type HydrationProps = {
  pagePath: string;
  layoutPaths: string[];
};

// used in the server, at Bun.build
export function encodeHydrationProps(props: HydrationProps): string {
  return JSON.stringify(props);
}

// used in the window
export function decodeHydrationProps(props: string): HydrationProps {
  return JSON.parse(props);
}
