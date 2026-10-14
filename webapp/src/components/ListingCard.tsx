// Lenta kartasi: kvadrat rasm, pastda masofa belgisi, sarlavha va narx (Karrot uslubida).

import type { Listing } from "../api/types";
import { useLang } from "../lib/i18n";
import { formatDistance, formatPrice } from "../lib/format";
import { conditionLabel, statusLabel } from "../lib/labels";
import { tap } from "../lib/telegram";

const STATUS_TINT: Record<string, string> = {
  sold: "badge-dark",
  reserved: "badge-brand",
  hidden: "badge-plain",
};

export function ListingCard({ listing, onOpen }: { listing: Listing; onOpen: (id: number) => void }) {
  const { t } = useLang();
  const cover = listing.images[0];
  const distance = formatDistance(listing.distance_m);

  return (
    <article
      className="card"
      role="button"
      tabIndex={0}
      onClick={() => {
        tap();
        onOpen(listing.id);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") onOpen(listing.id);
      }}
    >
      <div className="card-photo">
        {cover ? (
          <img src={cover.thumb_url} alt="" loading="lazy" />
        ) : (
          <span className="no-photo">{t("noPhoto")}</span>
        )}
        {distance && <span className="distance">{distance}</span>}
        {listing.status !== "active" && (
          <span className={`badge ${STATUS_TINT[listing.status] ?? ""}`}>{statusLabel(listing.status, t)}</span>
        )}
      </div>
      <h3 className="card-title">{listing.title}</h3>
      <p className="card-price">
        {formatPrice(listing.price, listing.price_type, { free: t("free"), negotiable: t("negotiable") })}
      </p>
      <p className="card-meta">{conditionLabel(listing.condition, t)}</p>
    </article>
  );
}
