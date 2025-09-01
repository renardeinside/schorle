import "@/app/global.css";
import { RootProvider } from "fumadocs-ui/provider";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
});

export default function Layout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.className}`} suppressHydrationWarning>
      <head>
        <link rel="icon" href="/logo.svg" type="image/svg+xml" />
        <meta
          name="description"
          content="Schorle is a hybrid framework that bridges Python backend development with modern React frontends. Keep your Python skills while building beautiful, interactive user interfaces."
        />
        <meta
          name="keywords"
          content="Python, React, FastAPI, TailwindCSS, MagicUI, Shadcn, Next.js, TypeScript"
        />
        <title>Schorle | Docs</title>
      </head>
      <body className="flex flex-col min-h-screen">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
