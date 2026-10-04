import type { Metadata } from "next";
import { Figtree, Geist_Mono } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/app-shell";
import { getAccount } from "@/lib/auth/account";

const figtree = Figtree({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    template: "%s | WildcatIQ",
    default: "WildcatIQ",
  },
  description: "WildcatIQ geology",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const account = await getAccount();
  return (
    <html
      lang="en"
      className={`${figtree.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <TooltipProvider>
          <AppShell account={account}>{children}</AppShell>
        </TooltipProvider>
        <Toaster />
      </body>
    </html>
  );
}
