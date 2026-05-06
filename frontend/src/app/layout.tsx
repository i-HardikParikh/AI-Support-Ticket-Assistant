import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Support AI — Agent Dashboard",
  description: "AI-powered support ticket triage, draft replies, and escalation detection.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

