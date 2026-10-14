#!/bin/sh
# Sertifikatni 12 soatda bir tekshiradi, yangilansa nginx'ni qayta yuklayadi.
# nginx asosiy jarayon bo'lib qoladi — shu sababli loop fonda ishga tushadi.
# (docker-entrypoint.d skriptlari faqat CMD `nginx` bo'lganda bajariladi.)

if [ -z "${SITE_DOMAIN:-}" ]; then
    echo "SITE_DOMAIN bo'sh — sertifikat yangilash o'tkazib yuborildi" >&2
    exit 0
fi

(
    while :; do
        sleep 43200
        if certbot renew --webroot -w /var/www/certbot --quiet; then
            nginx -s reload
        fi
    done
) &

exit 0
