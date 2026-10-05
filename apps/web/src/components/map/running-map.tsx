"use client";

import { useEffect, useRef } from "react";
import type { LayerGroup, Map as LeafletMap } from "leaflet";

type Point = {
  country_code: string;
  state: string | null;
  city: string | null;
  latitude: number;
  longitude: number;
  count: number;
};

export function RunningMap({ points, mode }: { points: Point[]; mode: "training" | "races" }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markersRef = useRef<LayerGroup | null>(null);

  useEffect(() => {
    let active = true;

    async function renderMap() {
      const leafletModule = await import("leaflet");
      const L = leafletModule.default;
      if (!active || !containerRef.current) return;

      if (!mapRef.current) {
        mapRef.current = L.map(containerRef.current, {
          center: [-15, -50],
          zoom: 3,
          minZoom: 2,
          worldCopyJump: true,
        });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 18,
        }).addTo(mapRef.current);
      }

      if (markersRef.current) mapRef.current.removeLayer(markersRef.current);
      const markers = L.layerGroup();
      const bounds: [number, number][] = [];

      for (const point of points) {
        if (!Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) continue;
        const coordinates: [number, number] = [point.latitude, point.longitude];
        bounds.push(coordinates);
        const icon = L.divIcon({
          className: "run-map-marker",
          html: `<span>${point.count}</span>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15],
        });
        const marker = L.marker(coordinates, { icon });
        const popup = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = point.city || point.state || point.country_code;
        const details = document.createElement("p");
        details.textContent = `${point.count} ${mode === "training" ? "atividades" : "provas"}${point.state ? ` · ${point.state}` : ""}`;
        popup.append(title, details);
        marker.bindPopup(popup);
        markers.addLayer(marker);
      }

      markersRef.current = markers;
      mapRef.current.addLayer(markers);
      if (bounds.length) mapRef.current.fitBounds(bounds, { padding: [35, 35], maxZoom: 8 });
      else mapRef.current.setView([-15, -50], 3);
      setTimeout(() => mapRef.current?.invalidateSize(), 0);
    }

    renderMap();
    return () => { active = false; };
  }, [points, mode]);

  useEffect(() => () => {
    mapRef.current?.remove();
    mapRef.current = null;
  }, []);

  return <div className="leaflet-running-map" ref={containerRef} />;
}
