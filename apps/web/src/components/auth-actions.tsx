"use client";

import { useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function AuthActions({ compact = false }: { compact?: boolean }) {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${apiUrl}/me`, { credentials: "include" })
      .then((response) => setAuthenticated(response.ok))
      .catch(() => setAuthenticated(false));
  }, []);

  if (compact) {
    return (
      <a className="button button-small" href={authenticated ? "/dashboard" : "/entrar"}>
        {authenticated ? "Meu Runverso" : "Entrar"}
      </a>
    );
  }

  if (authenticated) {
    return <a className="button" href="/dashboard">Abrir meu Runverso <b>→</b></a>;
  }

  return (
    <>
      <a className="button" href="/entrar">Criar meu Runverso <b>↗</b></a>
      <a className="button button-ghost" href="/entrar">Conectar com Strava</a>
    </>
  );
}
