import * as React from "react";
import type { JSX } from "react";

export type LayoutFC = (props: { children: React.ReactNode }) => JSX.Element;

/**
 * layouts must be ordered root → leaf (outermost first).
 * Example: [RootLayout, GroupLayout]
 */
export function wrapLayouts(
  Page: React.ComponentType,
  layouts: LayoutFC[],
): React.ReactElement {
  const tree = layouts.reduceRight<React.ReactNode>(
    (child, Layout) => <Layout>{child}</Layout>,
    <Page />,
  );
  return <>{tree}</>; // fragment avoids extra DOM element
}
