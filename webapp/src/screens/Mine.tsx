// Mening e'lonlarim: ixcham ro'yxat + holatni o'zgartirish.

import { useMine, useSetStatus } from "../api/hooks";
import type { Listing, ListingStatus } from "../api/types";
import { Notice } from "../components/States";
import { formatPrice } from "../lib/format";
import { type T, useLang } from "../lib/i18n";
import { statusLabel } from "../lib/labels";
import { tap } from "../lib/telegram";

const STATUSES: ListingStatus[] = ["active", "reserved", "sold", "hidden"];

function Row({ listing, onOpen, t }: { listing: Listing; onOpen: (id: number) => void; t: T }) {
  const setStatus = useSetStatus();
  const cover = listing.images[0];

  return (
    <div className="row-item">
      <button
        type="button"
        className="row-main"
        onClick={() => {
          tap();
          onOpen(listing.id);
        }}
      >
        {cover ? <img src={cover.thumb_url} alt="" loading="lazy" /> : <span className="thumb-empty" />}
        <span className="row-text">
          <span className="row-title">{listing.title}</span>
          <span className="row-price">
            {formatPrice(listing.price, listing.price_type, {
              free: t("free"),
              negotiable: t("negotiable"),
            })}
          </span>
        </span>
      </button>
      <select
        className="status-select"
        value={listing.status}
        disabled={setStatus.isPending}
        onChange={(event) =>
          setStatus.mutate({ id: listing.id, status: event.target.value as ListingStatus })
        }
      >
        {STATUSES.map((status) => (
          <option key={status} value={status}>
            {statusLabel(status, t)}
          </option>
        ))}
      </select>
    </div>
  );
}

export function Mine({ onOpen, onSell }: { onOpen: (id: number) => void; onSell: () => void }) {
  const { t } = useLang();
  const mine = useMine();

  if (mine.isError) {
    return (
      <Notice
        title={t("errorLoad")}
        text={String(mine.error.message)}
        action={{ label: t("retry"), onClick: () => void mine.refetch() }}
      />
    );
  }
  if (mine.isPending) return <Notice text={t("loading")} />;

  const items = mine.data ?? [];

  return (
    <div className="screen">
      <h1 className="screen-title">{t("mine")}</h1>
      {items.length === 0 ? (
        <Notice title={t("empty")} text={t("emptyHint")}>
          <button type="button" className="btn btn-primary" onClick={onSell}>
            {t("sell")}
          </button>
        </Notice>
      ) : (
        <div className="rows">
          {items.map((listing) => (
            <Row key={listing.id} listing={listing} onOpen={onOpen} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}
