// root layout for the app

import { ThemeProvider } from "@/components/theme/theme-provider";
import { Toaster } from "sonner";
import "@/styles/globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ThemeProvider>
      {children}
      <Toaster />
    </ThemeProvider>
  );
}
