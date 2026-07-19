# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

GEOrank 是面向 GEO（生成式引擎优化）的开源工作台：诊断网站/品牌在 AI 搜索中的可见性，并生成问答、方案、拓词和结构化内容。pnpm + Turborepo monorepo，前后端分离。

## 常用命令

前端 / SDK（仓库根，pnpm 10 + Turborepo）：

```bash
pnpm install
pnpm dev:web            # 前台 Next.js，端口 3010
pnpm dev:admin          # 管理台 Next.js
pnpm build              # turbo build 全部
pnpm typecheck          # turbo typecheck；也可 pnpm --filter @georank/web typecheck
pnpm lint               # turbo lint（eslint 9 flat config，见 eslint.config.mjs）
pnpm i18n:check         # 检查前端硬编码文案（提交前必跑）
```

单个前端测试（node --test，非 vitest/jest）：

```bash
pnpm test:admin-navigation      # 或 node --test tests/<file>.test.mjs 直接跑单文件
pnpm test:frontend-navigation
pnpm test:public-language
```

后端（`backend/`，Python 3.12，FastAPI）：

```bash
cd backend
python -m tests.run                              # 全量后端测试（unittest discover）
python -m unittest tests.test_ai_client          # 单个测试模块
python -m unittest tests.test_ai_client.ClassName.test_method   # 单个用例
```

本地全栈（Docker Compose）：

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Dev compose 把静态前台和 API 绑到 `127.0.0.1`（`GEORANK_FRONTEND_PORT` / `GEORANK_API_PORT`，本机默认约定 3009 / 8000）。

## OpenAPI SDK 契约

`packages/api-sdk` 是从后端 `/openapi.json` **生成**的 TS SDK，不要手改生成产物。后端 API 改动后：

```bash
pnpm sdk:refresh        # = sdk:pull（需 API 跑在 localhost:8000）+ sdk:generate
pnpm sdk:check          # CI 校验生成产物与 openapi 是否一致
```

## 数据库迁移（关键约束）

`migrate` 服务是**唯一的 schema owner**。Compose 启动时先跑一次性 `migrate`（`python -m app.scripts.migrate`，内部调 `alembic upgrade head`），到达 head 后 `api`/`worker`/`beat` 才启动。`docker compose ps` 里 `migrate` 显示 `Exited (0)` 是正常的。新增模型改动需在 `backend/alembic/` 建迁移，不要在应用启动时建表。详见 `docs/database-migrations.md`。

## 架构

三套前端并存，注意区分：

- **`dist/`** — 当前主力静态前台（HTML/JS，nginx 提供），也是 `frontend` 容器实际挂载的内容。`pnpm build:public-tailwind` 生成其 CSS。
- **`apps/web`** — Next.js 16 App Router 前台（2.0 迁移方向，端口 3010）。
- **`apps/admin`** — Next.js 管理台。

共享包 `packages/`：`api-sdk`（生成的 SDK）、`auth`（会话/页面守卫）、`i18n`（next-intl 路由与字典）、`ui`（前后台共享组件）。

后端 `backend/app/`：

- `api/routes/` — FastAPI 路由，按域分（companies / diagnostics / keywords / solutions / experts / content / admin / settings / usage / auth）。
- `services/` — 业务逻辑。`ai_client.py` + `ai_usage.py` 是 AI Provider 抽象（兼容 OpenAI 格式的 Chat/Embedding，支持后台 API 池、轮询、故障转移、额度控制）。`vector_store.py`（Qdrant）、`graph_store.py`（Neo4j）、`storage.py`（MinIO）。
- `models/` — SQLAlchemy 模型；`tasks/` — Celery 任务（`crawl` / `process` / `diagnose` / `runtime`，分队列）。爬虫在独立 `crawler` 容器（Playwright，`Dockerfile.crawler`）跑 `crawl` 队列。

数据服务栈：PostgreSQL、Redis（Celery broker）、Qdrant（向量）、Neo4j（知识图谱）、MinIO（对象存储）。生产入口是 Traefik，file provider 只读配置在 `infra/traefik/`。

## 开源边界（重要）

公开仓库只含代码、配置模板、demo 数据和内置公开首页/专家 fixture，**不含**真实 API Key、生产数据、用户问答、私有专家/教程内容包。改动涉及公开面时提交前必跑：

```bash
pnpm public:check       # 校验公开边界、资产、内容策略
```

发布候选另跑 `pnpm release:check`（契约 + SDK + public + i18n + typecheck + build）。`runtime/homepages/` 下大部分是 gitignored 的运行时资产，只有个别 release UUID 目录被 whitelist。私有内容目录（`data/private/`、`content/private/` 等）在 `.gitignore` 中排除。

## 约定

- 界面/文案默认简体中文，前端新增文案走 i18n 字典（勿硬编码，`pnpm i18n:check` 会拦）。
- `git commit` 仅在用户明确要求时执行；不主动 PR / push。Canonical repo：`github.com/yaojingang/GEORank`。
