// .schorle/app/[[...slug]]/page.tsx
import { notFound } from "next/navigation";
import { pageRegistry, wrapLayouts } from "@/app/registry.gen";

export default async function Handler({
  params,
}: {
  params: Promise<{ slug: string | string[] | undefined }>;
}) {
  const { slug } = await params;

  const pageKey = slug
    ? Array.isArray(slug)
      ? slug.join("/")
      : slug
    : "Index";
  const entry = pageRegistry[pageKey];

  if (entry) {
    const { layouts, Page } = entry;
    return wrapLayouts(Page, layouts);
  }

  notFound();
}
