"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Runner = {
  profile: {
    username: string | null;
    real_name: string | null;
    display_name: string | null;
    bio: string | null;
    avatar_url: string | null;
    city: string | null;
    state: string | null;
    country_code: string;
    started_running_year: number | null;
    favorite_distance: string | null;
  };
};
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

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const response = await fetch(`${apiUrl}/me/profile`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        real_name: form.get("real_name") || null,
        display_name: form.get("display_name"),
        bio: form.get("bio") || null,
        city: form.get("city") || null,
        state: form.get("state") || null,
        country_code: form.get("country_code") || "BR",
        started_running_year: Number(form.get("started_running_year")) || null,
        favorite_distance: form.get("favorite_distance") || null,
      }),
    });
    if (response.ok) {
      setRunner(await response.json());
      setMessage("Perfil atualizado.");
      const photo = form.get("avatar") as File;
      if (photo?.size) {
        const upload = new FormData();
        upload.append("photo", photo);
        const avatarResponse = await fetch(`${apiUrl}/me/avatar`, {
          method: "POST",
          credentials: "include",
          body: upload,
        });
        if (avatarResponse.ok) setRunner(await avatarResponse.json());
        else setMessage("Perfil salvo, mas a foto não foi aceita.");
      }
    } else {
      const error = await response.json();
      setMessage(error.detail ?? "Não foi possível salvar o perfil.");
    }
  }

  if (!runner || !privacy) return <main className="dashboard-loading">Carregando perfil…</main>;

  const visibility = (name: keyof Privacy, label: string) => <label>{label}<select name={name} defaultValue={String(privacy[name])}><option value="public">Público</option><option value="followers">Seguidores</option><option value="private">Privado</option></select></label>;

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="/mapa">Mapa da corrida</a><a href="/atividades">Atividades</a><a href="/conquistas">Recordes</a><a href="/comunidade">Comunidade</a><a className="active" href="/perfil">Perfil</a></nav></aside>
    <section className="dashboard-main achievements-main">
      <header className="activities-header"><div><span>IDENTIDADE DO CORREDOR</span><h1>Perfil e privacidade.</h1><p>Escolha como sua história aparece para outras pessoas.</p></div>{runner.profile.username && <a className="button" href={`/u/${runner.profile.username}`}>Ver perfil público</a>}</header>
      {message && <div className="sync-message">{message}</div>}
      <form className="race-form profile-form" onSubmit={saveProfile}>
        <h2>Dados públicos</h2>
        <div className="avatar-edit">{runner.profile.avatar_url ? <img src={`${apiUrl}${runner.profile.avatar_url}`} alt="Avatar" /> : <div>{runner.profile.display_name?.charAt(0).toUpperCase()}</div>}<label>Foto do perfil<input name="avatar" type="file" accept="image/jpeg,image/png,image/webp" /></label></div>
        <div className="form-row"><label>Nome de usuário<input name="username" defaultValue={runner.profile.username ?? ""} required /></label><label>Nome de exibição<input name="display_name" defaultValue={runner.profile.display_name ?? ""} required /></label></div>
        <label>Nome real <small>controlado pela opção “exibir nome real”</small><input name="real_name" defaultValue={runner.profile.real_name ?? ""} /></label>
        <label>Bio<textarea name="bio" rows={3} defaultValue={runner.profile.bio ?? ""} placeholder="Conte um pouco da sua história na corrida" /></label>
        <div className="form-row"><label>Cidade<input name="city" defaultValue={runner.profile.city ?? ""} /></label><label>Estado<input name="state" defaultValue={runner.profile.state ?? ""} /></label></div>
        <div className="form-row"><label>País<input name="country_code" defaultValue={runner.profile.country_code} maxLength={2} /></label><label>Corre desde<input name="started_running_year" type="number" min="1900" max={new Date().getFullYear()} defaultValue={runner.profile.started_running_year ?? ""} /></label></div>
        <label>Distância favorita<select name="favorite_distance" defaultValue={runner.profile.favorite_distance ?? ""}><option value="">Selecione</option><option>5K</option><option>10K</option><option>15K</option><option>21K</option><option>42K</option><option>ULTRA</option></select></label>
        <button className="button" type="submit">Salvar perfil</button>
      </form>
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
