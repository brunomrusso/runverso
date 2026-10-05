import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Runneverso — Sua história na corrida",
  description: "Provas, medalhas, mapas e histórias de quem corre.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
