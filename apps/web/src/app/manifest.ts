import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Runneverso",
    short_name: "Runneverso",
    description: "Sua história na corrida, reunida em um único lugar.",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#f4f1e8",
    theme_color: "#11120f",
    lang: "pt-BR",
    categories: ["sports", "health", "social"],
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
  };
}
