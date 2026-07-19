# GEO工作台

GEO工作台 is a workbench for Generative Engine Optimization (GEO). It diagnoses how visible your website and brand are in AI search, and turns those insights into Q&A, action plans, keyword assets, structured content tools, and a manageable knowledge base.

Diagnose first, then ask, then generate plans, then accumulate keywords, structured data, and a knowledge base.

## Core Features

| Module | Description |
|---|---|
| Company directory | Curate and manage GEO-related companies, tools, vendors, and cases with submission, review, publishing, and categorization |
| Website diagnostics | Inspect Schema, page structure, meta, readability, citation signals, and AI search visibility |
| AI Q&A | Generate structured answers about GEO, AI search, and brand visibility with company and diagnostic context |
| GEO plans | Produce actionable 30/60/90-day optimization plans from goals, site, resources, and constraints |
| Keyword workbench | Expand business terms into question, scenario, commercial-intent, and recommendation keywords |
| GEO tools | JSON-LD generator, llms.txt generator, AI-friendliness scoring, GEO title generator, knowledge-base generator |
| Experts channel | Public profiles, practice areas, and details of GEO/AI experts |
| Tutorials channel | GEO fundamentals, evaluation and governance, content structure, technical markup, and case studies |
| Admin console | Manage companies, diagnostics, Q&A, keywords, experts, tutorials, users, settings, the API pool, module toggles, and the custom homepage |

## Architecture

A monorepo with a static frontend, Next.js migration code, a FastAPI backend, and shared packages.

- **Frontend**: the 3009 static frontend (`dist/`) is the primary experience; the Next.js App Router migration (`apps/web`) is kept in parallel.
- **Admin**: Next.js admin console (`apps/admin`).
- **Backend**: FastAPI, SQLAlchemy, Alembic, Celery.
- **Data services**: PostgreSQL, Redis, Qdrant, Neo4j, MinIO.
- **AI layer**: OpenAI-compatible Chat and Embedding providers, with an admin-configurable API pool.
- **Tooling**: pnpm workspace, Turborepo, OpenAPI SDK, Docker Compose.

## Local Development

> Copy the environment template and fill in your own secrets before the first run.

```bash
pnpm install
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Frontend app
pnpm dev:web

# Admin console
pnpm dev:admin
```

Compose runs a one-shot `migrate` service first. The API and async workers start only after the database reaches the Alembic head; `migrate` showing `Exited (0)` in `docker compose ps` is expected. See [database migrations & startup](docs/database-migrations.md) for upgrades and recovery.

AI features require an OpenAI-compatible model API. Configure it in `.env` or in the admin settings API pool after the backend is running.

## API & Model Configuration

Supports OpenAI-compatible model services. The admin settings let you configure multiple providers, with:

- Encrypted API key storage.
- Base URL and model name configuration.
- Provider connectivity tests.
- API round-robin and failover.
- Quota control and user-supplied keys.

This repository ships no real API keys. Use your own model service and take responsibility for cost, privacy, and compliance.

## Disclaimer

GEO工作台 helps teams analyze and improve AI search visibility. It does not sell rankings, does not guarantee that any model will recommend a given brand, and does not represent any AI search platform.

## License

The software code is licensed under Apache-2.0. Expert profiles, names, likenesses, brands, and built-in homepage content are subject to additional rights — see [DATA_LICENSE.md](DATA_LICENSE.md).
