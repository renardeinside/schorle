import { type PropsWithChildren } from "react";

export type ManifestEntry = {
  css: string | null;
  js: string;
};

export type Manifest = Record<string, ManifestEntry>;

export type RootLayoutProps = PropsWithChildren<{
  cssPath: string | null;
}>;
