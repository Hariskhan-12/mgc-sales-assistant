import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "MGC Sales Assistant", description: "Internal sales tool for MGC Aurora Heights" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body className="bg-slate-50 min-h-screen">{children}</body></html>;
}
