import { DocsLayout } from "@/components/layout/docs";
import { baseOptions } from "@/lib/layout.shared";
import { source } from "@/lib/source";
import {
  Sidebar,
  SidebarPageTree,
  SidebarViewport,
} from "@/components/sidebar";

export default function Layout({ children }: LayoutProps<"/docs">) {
  return (
    <DocsLayout
      tree={source.pageTree}
      {...baseOptions()}
      leftSection={
        <Sidebar
          Content={
            <SidebarViewport className="h-full p-4">
              <SidebarPageTree />
            </SidebarViewport>
          }
        />
      }
    >
      {children}
    </DocsLayout>
  );
}
