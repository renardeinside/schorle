import "@/styles/globals.css";
import { Meta } from "@schorle/shared";
import { ThemeProvider } from "@schorle/shared";
import SchorleDevHelper from "@/components/dev/SchorleDevHelper";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Create a new query client instance
const queryClient = new QueryClient();

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
        <QueryClientProvider client={queryClient}>
          <ThemeProvider storageKey={storageKey}>{children}</ThemeProvider>
        </QueryClientProvider>
        <SchorleDevHelper />
      </body>
    </html>
  );
}
