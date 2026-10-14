#!/bin/sh
# Vaqtinchalik (o'zi-o'ziga imzo qo'ygan) sertifikat yaratadi — nginx :443
# server'i faylsiz ishga tushmaydi, haqiqiy sertifikat certbot olgunga qadar
# shu ishlaydi. Ishlatish: `sh deploy/nginx/tls-placeholder.sh localhost`
#
# Diqqat: volume nomi `<loyiha>_<volume>`, loyiha nomi `name:` dan (qoshni).

set -eu

domain="${1:?domen kerak: sh tls-placeholder.sh qoshni.example.com}"
volume="${QOSHNI_LETSENCRYPT_VOLUME:-qoshni_letsencrypt}"

docker run --rm \
    --entrypoint sh \
    -v "${volume}:/etc/letsencrypt" \
    alpine/openssl \
    -c "mkdir -p /etc/letsencrypt/live/${domain} && \
        openssl req -x509 -nodes -newkey rsa:2048 -days 90 \
            -subj '/CN=${domain}' \
            -addext 'subjectAltName=DNS:${domain}' \
            -keyout /etc/letsencrypt/live/${domain}/privkey.pem \
            -out /etc/letsencrypt/live/${domain}/fullchain.pem"

echo "${domain} uchun vaqtinchalik sertifikat ${volume} volume'ida yaratildi"
