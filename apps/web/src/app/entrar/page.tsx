"use client";

import { useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type AuthConfig = { google: boolean; strava: boolean };

export default function LoginPage() {
  const [config, setConfig] = useState<AuthConfig | null>(null);

  useEffect(() => {
    fetch(`${apiUrl}/config/auth`)
      .then((response) => response.json())
      .then(setConfig)
      .catch(() => setConfig({ google: false, strava: false }));
  }, []);

  return (
    <main className="auth-shell">
      <a className="brand" href="/">RUNNE<span>VERSO</span></a>
      <section className="auth-card">
        <div className="eyebrow"><i /> Entre no seu universo</div>
        <h1>Continue<br /><em>correndo.</em></h1>
        <p>Entre com uma conta segura. Você poderá conectar o outro provedor depois.</p>
        <div className="auth-actions">
          <a className={`provider google ${config?.google ? "" : "disabled"}`} href={`${apiUrl}/auth/google/login`}>
            <b>G</b> Continuar com Google
          </a>
          <a className={`provider strava ${config?.strava ? "" : "disabled"}`} href={`${apiUrl}/auth/strava/login`}>
            <b>↗</b> Continuar com Strava
          </a>
        </div>
        {config && !config.google && !config.strava && (
          <div className="setup-note">
            Configure as credenciais Google e Strava no arquivo <code>.env</code> para ativar os logins locais.
          </div>
        )}
        <small>Ao continuar, você concorda com os termos e a política de privacidade do Runneverso.</small>
      </section>
    </main>
  );
}
