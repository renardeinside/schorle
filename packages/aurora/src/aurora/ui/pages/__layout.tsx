import "@/styles/globals.css";
import { Meta } from "@schorle/shared";
import { ThemeProvider } from "@schorle/shared";
import SchorleDevHelper from "@/components/dev/SchorleDevHelper";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const storageKey = "theme";
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <Meta storageKey={storageKey} />
      </head>
      <body>
        <ThemeProvider storageKey={storageKey}>{children}</ThemeProvider>
        <SchorleDevHelper />
      </body>
    </html>
  );
}
