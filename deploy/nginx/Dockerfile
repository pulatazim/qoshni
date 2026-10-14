# Mini App + nginx + certbot — bitta image (context = repo ildosi):
#   docker build -f deploy/nginx/Dockerfile .
#
# Statik bundle yasab, nginx'ga beriladi; HTTPS sertifikatlari Let's Encrypt'dan
# olinadi (certbot ichkarida — alohida konteyner va docker socket kerak emas).

FROM node:24-alpine AS build

WORKDIR /app

COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY webapp/ ./
RUN npm run build

FROM nginx:1.27-alpine

# HTTP-01 tekshiruvi va sertifikat yangilash uchun.
RUN apk add --no-cache certbot

COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html
COPY deploy/nginx/templates/ /etc/nginx/templates/
COPY deploy/nginx/30-renew-loop.sh /docker-entrypoint.d/30-renew-loop.sh

EXPOSE 80 443
