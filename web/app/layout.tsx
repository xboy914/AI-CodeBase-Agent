import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Codebase Agent",
  description: "Grounded answers from your React and TypeScript codebase.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
