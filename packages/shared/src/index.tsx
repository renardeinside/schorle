import React from "react";
import type { JSX, ReactNode, ComponentType, ReactElement } from "react";
import { ThemeProvider } from "./theme-provider";
import { Meta } from "./Meta";
import { PropsProvider, useProps } from "./props";
import type { LayoutFC } from "./types";
import { useHeaders } from "./headers";
import { useCookies } from "./cookies";
import { type Dict } from "./types";

function wrapLayouts(Page: ComponentType, layouts: LayoutFC[]): ReactElement {
  // MDX components for proper prose styling
  const mdxComponents = {
    wrapper: ({ children }: { children: React.ReactNode }) => (
      <article className="prose prose-slate max-w-none dark:prose-invert">
        {children}
      </article>
    ),
  };

  // Create page element, checking if it's an MDX component
  const pageElement = (() => {
    // Check if Page is an MDX component and pass components accordingly
    if (Page.toString().includes("components") || Page.name === "MDXContent") {
      // @ts-ignore - MDX components accept a components prop but TypeScript doesn't know this
      return <Page components={mdxComponents} />;
    }
    return <Page />;
  })();

  // Wrap with layouts
  const tree = layouts.reduceRight<React.ReactNode>(
    (child, Layout) => <Layout>{child}</Layout>,
    pageElement,
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
  useHeaders,
  useCookies,
  type Dict,
};
