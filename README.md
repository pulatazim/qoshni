# Qo'shni

Qo'shnilar orasidagi e'lon bozori: odamlar uydagi keraksiz narsalarni bir bosishda e'lon
qiladi, qo'shnisi masofa va kategoriya bo'yicha topadi, chat orqali kelishib uchrashib
oladi. Telegram Mini App sifatida ishlaydi, to'lov platforma ichida emas — uchrashib naqd.

Muammo: Toshkentda kichik e'lon bozorlari mahalla Telegram guruhlarida cho'kib ketadi,
qidiruv yo'q, sotuvchiga ishonib bo'lmaydi. Qo'shni bitta tumandan boshlab masofa,
ishonch darajasi va moderatsiyani bitta joyga yig'adi.

[![CI](https://github.com/pulatazim/qoshni/actions/workflows/ci.yml/badge.svg)](https://github.com/pulatazim/qoshni/actions/workflows/ci.yml)

## Hozirgi holat

1-hafta (poydevor): FastAPI skeleti, PostGIS + Alembic, `docker compose`, CI.
Loyiha rejasi va texnik dizayn: [docs/Qoshni-MVP-texnik-dizayn.pdf](docs/Qoshni-MVP-texnik-dizayn.pdf).

## Tez ishga tushirish

Docker Desktop (WSL2 bilan) va `docker compose` v2.24+ kerak.

```bash
cp .env.example .env
cd deploy
docker compose up -d
docker compose exec api alembic upgrade head
curl http://localhost:8000/health
```

Docker'siz, faqat Python bilan (Postgres bazasiz testlar ishlaydi):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .[dev]
ruff check . && pytest
```

## Struktura

```
backend/    FastAPI ilovasi, SQLAlchemy modellari, Alembic, pytest
webapp/     React + Vite Mini App (7-haftada qo'shiladi)
deploy/     docker-compose, Caddy, zaxira skripti
docs/       arxitektura va ADR yozuvlari
```

## Test va lint

```bash
cd backend
uv run ruff check .
uv run pytest
```

CI har bir push'da `ruff`, `alembic upgrade head` (PostGIS'li Postgres service'da) va
`pytest` ni ishga tushiradi.

## Stack

FastAPI + SQLAlchemy 2 (async) + Alembic, PostgreSQL 16 (PostGIS, pg_trgm), Redis + ARQ,
aiogram, React 18 + Vite + TanStack Query. Asosiy qarorlar qisqacha `docs/adr/` da.
