import "@/styles/globals.css";
import { Meta } from "@schorle/shared";
import { ThemeProvider } from "@schorle/shared";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const storageKey = "theme";
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <Meta storageKey={storageKey} />
      </head>
      <body>
        <ThemeProvider storageKey={storageKey}>{children}</ThemeProvider>
      </body>
    </html>
  );
}
