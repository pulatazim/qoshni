#!/usr/bin/env bash
# Kunlik pg_dump -> Cloudflare R2. VM'da cron orqali ishga tushadi:
# 0 3 * * * /opt/qoshni/deploy/backup.sh >> /var/log/qoshni-backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

mkdir -p backups
dump="qoshni-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"

docker compose -f deploy/docker-compose.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=plain --no-owner | gzip > "backups/$dump"

AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
  aws s3 cp "backups/$dump" "s3://$R2_BUCKET/backups/$dump" \
  --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"

rm "backups/$dump"
echo "zaxira yuklandi: $dump"
