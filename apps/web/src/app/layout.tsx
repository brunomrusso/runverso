import type { Metadata, Viewport } from "next";
import "flag-icons/css/flag-icons.min.css";
import "leaflet/dist/leaflet.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Runneverso — Sua história na corrida",
  description: "Provas, medalhas, mapas e histórias de quem corre.",
  applicationName: "Runneverso",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Runneverso",
  },
};

export const viewport: Viewport = {
  themeColor: "#11120f",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
