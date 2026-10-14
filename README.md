# Qo'shni

Qo'shnilar orasidagi e'lon bozori: odamlar uydagi keraksiz narsalarni bir bosishda e'lon
qiladi, qo'shnisi masofa va kategoriya bo'yicha topadi, chat orqali kelishib uchrashib
oladi. Telegram Mini App sifatida ishlaydi, to'lov platforma ichida emas — uchrashib naqd.

Muammo: Toshkentda kichik e'lon bozorlari mahalla Telegram guruhlarida cho'kib ketadi,
qidiruv yo'q, sotuvchiga ishonib bo'lmaydi. Qo'shni bitta tumandan boshlab masofa,
ishonch darajasi va moderatsiyani bitta joyga yig'adi.

[![CI](https://github.com/pulatazim/qoshni/actions/workflows/ci.yml/badge.svg)](https://github.com/pulatazim/qoshni/actions/workflows/ci.yml)

## Hozirgi holat

1-hafta (poydevor) — **tayyor**: FastAPI skeleti (`/health`), PostGIS + pg_trgm bilan
birinchi migratsiya, `docker compose` (postgres + redis + api), GitHub Actions CI.
Lokal `docker compose up -d` bilan ko'tarilib, migratsiya va `/health` ishlagani tekshirildi.

2-hafta (autentifikatsiya) — **tayyor**: `verify_init_data` (HMAC-SHA256), `POST /auth/telegram`
→ JWT, `get_current_user`, `users` jadvali, `GET/PATCH /me`, `PUT /me/location` (~300 m
xiralashtirish), yagona xato formati `{"error": {"code", "message"}}`.

2.5 (seed) — **tayyor**: Toshkentning 12 tumani va 14 kategoriya `python -m seeds.seed`
orqali idempotent ravishda yukiladi.

3–6-hafta (e'lon bozori) — birinchi qismi **tayyor**: `listings` va `listing_images`
jadvallari (GiST — masofa, GIN trigram — qidiruv, qisman indeks — lenta saralashi),
`POST /listings`, `GET /listings` (radius + filtrlar + `q` qidiruvi + cursor sahifalash),
`GET /listings/mine`, `GET /listings/{id}` (ko'rishlar hisobi bilan),
`POST /listings/{id}/status`, `DELETE /listings/{id}`. Qidiruv kirill/lotin normalizatsiyasi
bilan ishlaydi: "китоб" so'rovi "kitob" e'lonini topadi.

Rasm quvuri ham **tayyor**: `POST /listings/{id}/images` (multipart) → EXIF/GPS tozalanadi,
burilish piksellarga singdiriladi, WebP'ning ikki ko'rinishi (1080 ochilish + 400 lenta)
Cloudflare R2'ga yoziladi; `DELETE /listings/{id}/images/{image_id}` ikkala obyektni
o'chiradi. Bitta e'londa 6 tagacha rasm. R2 kalitlari bo'lmasa ish xotira saqlagichida
davom etadi (`app/core/storage.py`), shuning uchun testlar tarmoqqa chiqmaydi.

Qolgan qismi: rate limit (Redis) va moderatsiya filtri.

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

API testlari (`/auth/telegram`, `/me`, `/listings`) PostGIS bazasini talab qiladi —
`TEST_DATABASE_URL` berilsa ular ishlaydi, berilmasa o'tkazib yuboriladi:

```bash
docker compose -f deploy/docker-compose.yml exec postgres createdb -U qoshni qoshni_test
TEST_DATABASE_URL=postgresql+asyncpg://qoshni:qoshni@localhost:5432/qoshni_test pytest
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
