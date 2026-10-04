# Runverso

## Execução local

- Subir: `docker compose up --build`
- Testar API: `docker compose exec api pytest`
- Lint API: `docker compose exec api ruff check .`
- Build web: `docker compose exec web npm run build`
- Migrations: `docker compose exec api alembic upgrade head`

## Convenções

- Documentação e interface em português do Brasil.
- Backend em FastAPI, SQLAlchemy 2 e Alembic.
- Frontend em Next.js e TypeScript estrito.
- PostgreSQL/PostGIS é o banco padrão, inclusive localmente.
- Conteúdo importado nunca deve se tornar público automaticamente.
- Segredos ficam em `.env`, que não deve ser versionado.
