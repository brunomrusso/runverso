"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Runner = {
  email: string;
  profile: { display_name: string | null; username: string | null; favorite_distance: string | null };
  strava_connected: boolean;
};

const cards = [
  { value: "0", label: "Provas", detail: "Cadastre sua primeira prova" },
  { value: "0", label: "Medalhas", detail: "Seu porta-medalhas espera por você" },
  { value: "0", label: "Países", detail: "Seu mapa começa aqui" },
  { value: "—", label: "Melhor marca", detail: "Conecte uma atividade" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [runner, setRunner] = useState<Runner | null>(null);

  useEffect(() => {
    fetch(`${apiUrl}/me`, { credentials: "include" })
      .then((response) => {
        if (!response.ok) throw new Error("unauthorized");
        return response.json();
      })
      .then((data) => {
        if (!data.profile.onboarding_completed) router.replace("/onboarding");
        else setRunner(data);
      })
      .catch(() => router.replace("/entrar"));
  }, [router]);

  async function logout() {
    await fetch(`${apiUrl}/auth/logout`, { method: "POST", credentials: "include" });
    router.replace("/");
  }

  if (!runner) return <main className="dashboard-loading">Carregando seu Runverso…</main>;

  return (
    <main className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <a className="brand" href="/">RUN<span>VERSO</span></a>
        <nav className="side-nav">
          <a className="active" href="/dashboard">Visão geral</a>
          <a href="#">Minhas provas</a>
          <a href="#">Porta-medalhas</a>
          <a href="#">Mapa da corrida</a>
          <a href="#">Atividades</a>
        </nav>
        <button onClick={logout}>Sair</button>
      </aside>
      <section className="dashboard-main">
        <header className="dashboard-header"><div><span>OLÁ, {runner.profile.username?.toUpperCase()}</span><h1>Bem-vindo ao<br /><em>seu Runverso.</em></h1></div><div className="avatar">{runner.profile.display_name?.charAt(0).toUpperCase()}</div></header>
        <div className="dashboard-stats">{cards.map((card) => <article key={card.label}><strong>{card.value}</strong><h2>{card.label}</h2><p>{card.detail}</p></article>)}</div>
        <section className="next-step"><div><span>PRÓXIMO PASSO</span><h2>{runner.strava_connected ? "Importe suas primeiras atividades" : "Conecte seu Strava"}</h2><p>Transforme seu histórico de corrida em provas, recordes e lugares conquistados.</p></div><a className="button" href={runner.strava_connected ? "#" : `${apiUrl}/auth/strava/login`}>{runner.strava_connected ? "Ver atividades" : "Conectar Strava"} <b>→</b></a></section>
      </section>
    </main>
  );
}
