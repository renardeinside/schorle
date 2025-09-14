import type { JSX, ReactNode, ComponentType, ReactElement } from "react";
import { ThemeProvider } from "./theme-provider";
import { Meta } from "./Meta";
import { PropsProvider, useProps } from "./props";
type LayoutFC = (props: { children: ReactNode }) => JSX.Element;

function wrapLayouts(Page: ComponentType, layouts: LayoutFC[]): ReactElement {
  const tree = layouts.reduceRight<React.ReactNode>(
    (child, Layout) => <Layout>{child}</Layout>,
    <Page />,
  );
  return <>{tree}</>; // fragment avoids extra DOM element
}

export {
  ThemeProvider,
  wrapLayouts,
  type LayoutFC,
  Meta,
  PropsProvider,
  useProps,
};
