import type { JSX, ReactNode, ComponentType, ReactElement } from "react";

export type LayoutFC = (props: { children: ReactNode }) => JSX.Element;

export function wrapLayouts(
  Page: ComponentType,
  layouts: LayoutFC[],
): ReactElement {
  const tree = layouts.reduceRight<React.ReactNode>(
    (child, Layout) => <Layout>{child}</Layout>,
    <Page />,
  );
  return <>{tree}</>; // fragment avoids extra DOM element
}
