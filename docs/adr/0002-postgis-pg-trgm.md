# 2. Geo va qidiruv uchun bitta Postgres

Status: qabul qilingan (2026-10-13)

Masofa so'rovi `PostGIS` (`ST_DWithin`, `ST_Distance`) bilan, matnli qidiruv `pg_trgm`
GIN indeksi va `similarity()` bilan bir xil bazada bajariladi. Elasticsearch yoki
Meilisearch qo'shish alohida servis, alohida indekslash quvuri va alohida xato turi
deganidir; 100 000 elongacha Postgres yetadi.

Kirill va lotin yozuvini bitta `normalize()` funksiyasi qaytaradi (e'lon saqlanganda ham,
so'rovda ham), shunda ikki alifbo bir indeksdan foydalanadi. Chegara — so'rov kechikishi
sezilar bo'lsa Meilisearch qo'shiladi.
