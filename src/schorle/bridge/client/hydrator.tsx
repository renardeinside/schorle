import { hydrateRoot } from "react-dom/client";
import { wrapLayouts, type HydrationProps } from "@schorle/bridge/shared";

// @ts-ignore
import { registry } from "@/registry";

declare global {
  interface Window {
    __SCHORLE_HYDRATION_PROPS__: HydrationProps; // { pageId, layoutIds }
  }
}

type RegistryKey = keyof typeof registry;

async function loadRegistryEntry(key: RegistryKey) {
  const loader = registry[key];
  if (!loader) {
    console.error(`No registry entry for "${String(key)}"`);
    console.log(
      `Available registry entries: ${Object.keys(registry).join(", ")}`,
    );
    console.log(`Total entries: ${Object.keys(registry).length}`);
    throw new Error(`No registry entry for "${String(key)}"`);
  }
  const mod = await loader();
  return mod.default;
}

async function loadAndHydrate() {
  const { pagePath, layoutPaths } = window.__SCHORLE_HYDRATION_PROPS__;
  const Page = await loadRegistryEntry(
    pagePath.split("/").pop()!.replace(".tsx", "") as RegistryKey,
  );
  const layouts = await Promise.all(
    layoutPaths.map((layoutPath) =>
      loadRegistryEntry(
        layoutPath.split("/").pop()!.replace(".tsx", "") as RegistryKey,
      ),
    ),
  );
  hydrateRoot(document, wrapLayouts(Page, layouts));
}

loadAndHydrate();
