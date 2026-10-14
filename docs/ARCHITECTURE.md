# Arxitektura

Modulli monolit: bitta FastAPI ilovasi va bitta fon worker'i, ikkalasi bitta VM'da Docker
Compose orqali. 10 000 faol foydalanuvchigacha ikkinchi servisga o'tish talab qilinmaydi.

## Qatlam

```
Telegram Mini App (React)  ->  Caddy (HTTPS, statik)  ->  FastAPI (/api/v1, /ws)
                                                              |
                     Redis (kesh, pub/sub)  <---------  PostgreSQL 16 + PostGIS + pg_trgm
                                                              |
                                    ARQ worker  ->  Telegram bot (aiogram) -> offline foydalanuvchi
```

Rasmlar: backend Cloudflare R2 ga yozadi, foydalanuvchi Cloudflare CDN orqali oladi.

## Kod tuzilishi

- `app/core/` — sozlamalar, async engine, Redis, JWT va Telegram initData tekshiruvi.
- `app/modules/<usta>/` — `router.py`, `service.py`, `schemas.py`. Modul faqat o'z
  jadvaliga yozadi; boshqa modulga kerak bo'lsa, uning service'ini chaqiradi.
- `app/models/` — SQLAlchemy modellari, migratsiyalar `migrations/` da.
- `app/admin/` — SQLAdmin moderatsiya paneli.
- `app/worker.py` — ARQ vazifalari (bildirishnomalar, keyin rasm qayta ishlash).

## Ma'lumot oqimi

- Har bir so'rov `Authorization: Bearer <JWT>` bilan keladi; JWT faqat Telegram initData
  HMAC tekshiruvidan o'tgach beriladi.
- Ro'yxatlar cursor pagination bilan (`?cursor=...&limit=20`), offset ishlatilmaydi.
- Xabar avval Postgres'ga yoziladi, keyin Redis pub/sub orqali ulangan mijozlarga
  tarqaladi. Redis o'chsa ham xabar yo'qolmaydi; oflayn foydalanuvchiga ARQ vazifasi bot
  orqali xabar beradi (bitta chat bo'yicha 5 daqiqada bir martadan ko'p emas).
- Koordinatalar `GEOGRAPHY` turida, saqlashdan oldin ~300 m katakka yaxlitlanadi.
- Narx `BIGINT` so'mda; `float` hech qachon ishlatilmaydi.
- E'lon va foydalanuvchi `deleted_at` orqali soft delete qilinadi.

## Hozirgi qamrov (6-hafta)

Ishlaydi: `/health`, PostGIS/pg_trgm migratsiyalari, seed (12 tuman, 14 kategoriya),
auth (initData → JWT), profil va xiralashtirilgan joylashuv, e'lon bozori (geo-lenta,
filtrlar, qidiruv, cursor sahifalash, holat, soft delete), rasm quvuri (EXIF tozalash,
WebP 1080/400, Cloudflare R2), so'rov/e'lon cheklovi va moderatsiya filtri.
Compose orqali Postgres/Redis, CI (ruff + alembic + pytest).
Keyingi haftalarda qo'shiladi: Mini App (React/Vite), chat/websocket, ishonch
reytingi va qo'shimcha moderatsiya, Sentry va zaxira.
