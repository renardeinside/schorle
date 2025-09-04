export const registry = {
  "Index": () => import("@/pages/Index.tsx"),
  "__layout": () => import("@/pages/__layout.tsx")
} as const;
