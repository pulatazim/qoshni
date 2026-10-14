# Arxitektura

Modulli monolit: bitta FastAPI ilovasi va bitta fon worker'i, ikkalasi bitta VM'da Docker
Compose orqali. 10 000 faol foydalanuvchigacha ikkinchi servisga o'tish talab qilinmaydi.

## Qatlam

```
Telegram Mini App (React)  ->  nginx (HTTPS, statik)  ->  FastAPI (/api/v1, /ws)
                                                              |
                     Redis (kesh, pub/sub)  <---------  PostgreSQL 16 + PostGIS + pg_trgm
                                                              |
                                    ARQ worker  ->  Telegram bot (aiogram) -> offline foydalanuvchi
```

Rasmlar: backend Cloudflare R2 ga yozadi, foydalanuvchi Cloudflare CDN orqali oladi.

## Frontend qanday beriladi

- Ishlab chiqishda: `webapp` servisi (vite dev server, `docker-compose.yml`) va `/api`
  so'rovlarini `QOSHNI_API_TARGET`ga proksilaydi.
- Production'da: `deploy/nginx/Dockerfile` bitta image yasaydi — statik bundle
  (`npm run build`) + nginx + certbot. Sayt konfiguratsiyasi
  `deploy/nginx/templates/default.conf.template`: `SITE_DOMAIN` muhit o'zgaruvchisi bilan
  almashtiriladi, `:80` faqat `/.well-known` ni berib `:443`ga buradi, `:443` SPA'ni
  (`try_files ... /index.html`), `/api/` va `/health` ni `api:8000`ga proksilaydi,
  `client_max_body_size 12m` (rasm yuklash chegarasi). Sertifikat papkasi
  `/etc/letsencrypt/live/<SITE_DOMAIN>/` — `letsencrypt` va `certbot_www` volume'larida,
  host fayllarida emas. `30-renew-loop.sh` 12 soatda bir tekshiradi, yangilansa
  `nginx -s reload` qiladi (shu sababli CMD `nginx` bo'lishi kerak: nginx entrypoint'i
  `/docker-entrypoint.d` skriptlarini faqat shunda bajaradi).

## Kod tuzilishi

- `app/core/` — sozlamalar, async engine, Redis, JWT va Telegram initData tekshiruvi.
- `app/modules/<usta>/` — `router.py`, `service.py`, `schemas.py`. Modul faqat o'z
  jadvaliga yozadi; boshqa modulga kerak bo'lsa, uning service'ini chaqiradi.
- `app/models/` — SQLAlchemy modellari, migratsiyalar `migrations/` da.
- `app/bot/` — aiogram servisi: Mini App'ga kirish tugmalari va matnlar (uz/ru). Suhbat
  mantiqi yo'q — bot foydalanuvchini ilovaga yetkazadi, keyin bildirishnoma kanali bo'ladi.
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

## Hozirgi qamrov (8-hafta)

Ishlaydi: `/health`, PostGIS/pg_trgm migratsiyalari, seed (12 tuman, 14 kategoriya),
auth (initData → JWT), profil va xiralashtirilgan joylashuv, e'lon bozori (geo-lenta,
filtrlar, qidiruv, cursor sahifalash, holat, soft delete), rasm quvuri (EXIF tozalash,
WebP 1080/400, Cloudflare R2), so'rov/e'lon cheklovi va moderatsiya filtri.
Compose orqali Postgres/Redis, CI (ruff + alembic + pytest).

Frontend (`webapp/`): React 18 + Vite + TypeScript + TanStack Query, router kutubxonasiz —
ekran stek'i `App.tsx` da ushlanadi va Telegram `BackButton` shu stek'dan chiqaradi.
- `src/api/types.ts` — backend sxemalari bilan kelishilgan turlar; `Backend` interfeysi
  orqali HTTP (`http.ts`) va demo (`mock.ts`) almashinadi.
- `src/api/http.ts` — `/api/v1` so'rovlari, JWT sessionStorage'da, xato konverti
  `ApiError`ga aylantiriladi; `src/api/hooks.ts` — query/mutation hooklari.
- `src/lib/` — `telegram.ts` (SDK qobiq), `i18n.ts` (uz/ru), `format.ts`, `labels.ts`, `geo.ts`.
- `src/screens/` — Feed, ListingView, Create, Mine, Profile; `src/components/` — karta,
  chip, pastki panel, holat bloki. Uslub `src/styles.css` (Karrot: #ff5c39, kartochkali
  setka, masofa belgisi, xavfsiz hududlar).

Brauzerda `?live=1` bo'lmasa demo rejim yoqiladi (`shouldUseMock()`), shuning uchun
UI Telegram'siz ham ko'riladi. Vite `/api` ni `QOSHNI_API_TARGET`ga proksilaydi — CORS
sozlamasi talab qilinmaydi.

Keyingi haftalarda qo'shiladi: chat/websocket, bot orqali bildirishnomalar (yangi xabar,
e'lon holati), ishonch reytingi va qo'shimcha moderatsiya, Sentry va zaxira.

Bot (`app/bot/`) long polling bilan ishlaydi — webhook uchun HTTPS domen hozircha kerak
emas. Mini App manzili `WEBAPP_URL` dan olinadi: u bo'sh bo'lsa `/app` matn bilan javob
qaytaradi va menyu tugmasi o'rnatilmaydi. Sozlash Telegram'ga `python -m app.bot.setup`
orqali yoziladi (buyruqlar uz/ru, menyu tugmasi).
