// E'lon tafsiloti: katta rasm, narx, tavsif, sotuvchi va amal tugmalari.

import { useListing, useSetStatus } from "../api/hooks";
import type { ListingStatus, Profile } from "../api/types";
import { Notice } from "../components/States";
import { formatDistance, formatPrice } from "../lib/format";
import { useLang } from "../lib/i18n";
import { conditionLabel, statusLabel } from "../lib/labels";
import { tap } from "../lib/telegram";

const OWN_ACTIONS: ListingStatus[] = ["reserved", "sold", "hidden", "active"];

export function ListingView({ id, me, onBack }: { id: number; me: Profile; onBack: () => void }) {
  const { t } = useLang();
  const listing = useListing(id);
  const setStatus = useSetStatus();

  if (listing.isError) {
    return (
      <Notice
        title={t("errorLoad")}
        text={String(listing.error.message)}
        action={{ label: t("retry"), onClick: () => void listing.refetch() }}
      />
    );
  }
  if (listing.isPending) return <Notice text={t("loading")} />;

  const data = listing.data;
  const cover = data.images[0];
  const distance = formatDistance(data.distance_m);
  const isOwner = data.seller_id === me.id;

  return (
    <div className="screen">
      <div className="sub-head">
        <button type="button" className="back" onClick={onBack}>
          ‹ {t("back")}
        </button>
      </div>

      <div className="detail-photo">
        {cover ? <img src={cover.url} alt="" /> : <span className="no-photo">{t("noPhoto")}</span>}
        {data.status !== "active" && <span className="badge badge-dark">{statusLabel(data.status, t)}</span>}
      </div>

      <h1 className="detail-title">{data.title}</h1>
      <p className="detail-price">
        {formatPrice(data.price, data.price_type, { free: t("free"), negotiable: t("negotiable") })}
      </p>
      <p className="detail-meta">
        {conditionLabel(data.condition, t)}
        {distance ? ` · ${distance}` : ""}
        {` · ${t("views")}: ${data.view_count}`}
      </p>

      {data.description && <p className="detail-text">{data.description}</p>}

      <div className="seller">
        <div className="avatar">{(isOwner ? me.display_name : t("neighbor")).slice(0, 1)}</div>
        <div>
          <p className="seller-name">{isOwner ? me.display_name : t("neighbor")}</p>
          {isOwner && <p className="note">{t("trust")}: {me.trust_score}</p>}
        </div>
      </div>

      <div className="actions">
        {isOwner ? (
          OWN_ACTIONS.map((status) => (
            <button
              key={status}
              type="button"
              className={`btn ${status === "active" ? "btn-primary" : "btn-ghost"}`}
              disabled={setStatus.isPending || data.status === status}
              onClick={() => {
                tap("medium");
                setStatus.mutate({ id: data.id, status });
              }}
            >
              {statusLabel(status, t)}
            </button>
          ))
        ) : (
          <>
            <button type="button" className="btn btn-primary" disabled>
              {t("writeSeller")}
            </button>
            <p className="note">{t("chatSoon")}</p>
          </>
        )}
      </div>
    </div>
  );
}
