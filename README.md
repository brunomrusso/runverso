# Runverso

Sua história na corrida, reunida em um único lugar.

O Runverso é uma comunidade para corredores organizarem provas, medalhas, recordes e os lugares onde já correram. O produto terá integração com Strava, porta-medalhas digital, mapas de provas e treinos e controles granulares de privacidade.

## Stack

- Frontend: Next.js, React e TypeScript
- Backend: Python, FastAPI e SQLAlchemy
- Banco: PostgreSQL com PostGIS
- Migrations: Alembic
- Ambiente local: Docker Compose

## Pré-requisitos

- Docker Desktop com Docker Compose
- Git

## Executar localmente

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Acesse:

- Aplicação: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Saúde da API: http://localhost:8000/health
- Saúde do banco: http://localhost:8000/health/database

## Testes e qualidade

```powershell
docker compose exec api pytest
docker compose exec api ruff check .
docker compose exec web npm run build
```

## Estrutura

```text
apps/api     API FastAPI, modelos, migrations e testes
apps/web     Aplicação web responsiva em Next.js
storage      Uploads locais ignorados pelo Git
docs         Documentação do produto
```

## Estado atual

A fundação local contém a landing page responsiva, API de saúde, PostgreSQL/PostGIS e a primeira migration da entidade de usuário. Autenticação com Google e Strava será a próxima etapa.
