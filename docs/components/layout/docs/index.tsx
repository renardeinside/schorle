import type { PageTree } from "fumadocs-core/server";
import React, { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "../../../lib/cn";
import { type BaseLayoutProps } from "../shared/index";
import { TreeContextProvider } from "fumadocs-ui/contexts/tree";
import { NavProvider } from "fumadocs-ui/contexts/layout";
import { Header } from "../home/index";

export interface DocsLayoutProps extends BaseLayoutProps {
  tree: PageTree.Root;

  /**
   * Props for the `div` container
   */
  containerProps?: HTMLAttributes<HTMLDivElement>;

  /**
   * Content for the left section (w-96)
   */
  leftSection?: ReactNode;
}

export function DocsLayout({
  nav = {},
  searchToggle = {},
  disableThemeSwitch = false,
  themeSwitch = { enabled: !disableThemeSwitch },
  i18n = false,
  children,
  leftSection,
  ...props
}: DocsLayoutProps) {
  return (
    <TreeContextProvider tree={props.tree}>
      <NavProvider>
        <main id="nd-docs-layout" className="flex flex-1 flex-col pt-14">
          {/* Use the same Header as home layout */}
          <Header
            links={props.links}
            nav={nav}
            themeSwitch={themeSwitch}
            searchToggle={searchToggle}
            i18n={i18n}
            githubUrl={props.githubUrl}
          />

          {/* Main content area with left section */}
          <div
            className="flex flex-1"
            style={
              { "--fd-left-sidebar-width": "12rem" } as React.CSSProperties
            }
          >
            {/* Left section with w-48 width */}
            <aside className="w-48">{leftSection}</aside>

            {/* Main content */}
            <div
              {...props.containerProps}
              className={cn(
                "flex-1 xl:[--fd-toc-width:286px]",
                props.containerProps?.className,
              )}
            >
              {children}
            </div>
          </div>
        </main>
      </NavProvider>
    </TreeContextProvider>
  );
}

// Re-export types that might be used elsewhere
export type { BaseLayoutProps } from "../shared/index";
