"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Runner = { profile: { username: string | null; display_name: string | null } };
type Privacy = {
  profile_visibility: "public" | "followers" | "private";
  activities_visibility: "public" | "followers" | "private";
  races_visibility: "public" | "followers" | "private";
  medals_visibility: "public" | "followers" | "private";
  photos_visibility: "public" | "followers" | "private";
  locations_visibility: "public" | "followers" | "private";
  show_real_name: boolean;
  show_times: boolean;
  approve_followers: boolean;
};

export default function ProfileSettingsPage() {
  const router = useRouter();
  const [runner, setRunner] = useState<Runner | null>(null);
  const [privacy, setPrivacy] = useState<Privacy | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${apiUrl}/me`, { credentials: "include" }),
      fetch(`${apiUrl}/me/privacy`, { credentials: "include" }),
    ]).then(async ([userResponse, privacyResponse]) => {
      if (!userResponse.ok) return router.replace("/entrar");
      setRunner(await userResponse.json());
      setPrivacy(await privacyResponse.json());
    });
  }, [router]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      profile_visibility: form.get("profile_visibility"),
      activities_visibility: form.get("activities_visibility"),
      races_visibility: form.get("races_visibility"),
      medals_visibility: form.get("medals_visibility"),
      photos_visibility: form.get("photos_visibility"),
      locations_visibility: form.get("locations_visibility"),
      show_real_name: form.get("show_real_name") === "on",
      show_times: form.get("show_times") === "on",
      approve_followers: form.get("approve_followers") === "on",
    };
    const response = await fetch(`${apiUrl}/me/privacy`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setMessage(response.ok ? "Privacidade atualizada." : "Não foi possível salvar.");
  }

  if (!runner || !privacy) return <main className="dashboard-loading">Carregando perfil…</main>;

  const visibility = (name: keyof Privacy, label: string) => <label>{label}<select name={name} defaultValue={String(privacy[name])}><option value="public">Público</option><option value="followers">Seguidores</option><option value="private">Privado</option></select></label>;

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="/mapa">Mapa da corrida</a><a href="/atividades">Atividades</a><a href="/conquistas">Recordes</a><a className="active" href="/perfil">Perfil</a></nav></aside>
    <section className="dashboard-main achievements-main">
      <header className="activities-header"><div><span>IDENTIDADE DO CORREDOR</span><h1>Perfil e privacidade.</h1><p>Escolha como sua história aparece para outras pessoas.</p></div>{runner.profile.username && <a className="button" href={`/u/${runner.profile.username}`}>Ver perfil público</a>}</header>
      {message && <div className="sync-message">{message}</div>}
      <form className="race-form privacy-form" onSubmit={save}>
        <h2>Visibilidade</h2>
        <p>Seu link público é <strong>{runner.profile.username ? `/u/${runner.profile.username}` : "criado ao definir um nome de usuário"}</strong>. O perfil só aparece quando estiver público.</p>
        <div className="form-row">{visibility("profile_visibility", "Perfil")}{visibility("activities_visibility", "Atividades")}</div>
        <div className="form-row">{visibility("races_visibility", "Provas e recordes")}{visibility("medals_visibility", "Medalhas")}</div>
        <div className="form-row">{visibility("photos_visibility", "Fotos")}{visibility("locations_visibility", "Mapa e lugares")}</div>
        <label className="check-option"><input name="show_real_name" type="checkbox" defaultChecked={privacy.show_real_name} /> Exibir nome real</label>
        <label className="check-option"><input name="show_times" type="checkbox" defaultChecked={privacy.show_times} /> Exibir tempos e recordes</label>
        <label className="check-option"><input name="approve_followers" type="checkbox" defaultChecked={privacy.approve_followers} /> Aprovar novos seguidores</label>
        <button className="button" type="submit">Salvar privacidade</button>
      </form>
    </section>
  </main>;
}
