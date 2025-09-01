import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import Logo from "@/components/Logo";

/**
 * Shared layout configurations
 *
 * you can customise layouts individually from:
 * Home Layout: app/(home)/layout.tsx
 * Docs Layout: app/docs/layout.tsx
 */
export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: <Logo className="flex items-center gap-2" />,
    },
    // see https://fumadocs.dev/docs/ui/navigation/links
    links: [],
    githubUrl: "https://github.com/renardeinside/schorle",
  };
}
