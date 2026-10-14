// Lenta: radius/kategoriya/qidiruv filtrlari va ikki ustunli kartalar.

import { useEffect, useMemo, useState } from "react";
import { useCategories, useDistricts, useFeedPages, useSetLocation, defaultFeedQuery } from "../api/hooks";
import type { Coordinates, FeedSort, Profile } from "../api/types";
import { Chip, ChipRow } from "../components/Chip";
import { ListingCard } from "../components/ListingCard";
import { Notice } from "../components/States";
import { useLang } from "../lib/i18n";
import { askPosition } from "../lib/geo";
import { tap } from "../lib/telegram";

const RADII = [1000, 3000, 7000, 20000];
const SORTS: FeedSort[] = ["new", "cheap", "expensive"];

export function Feed({ profile, onOpen }: { profile: Profile; onOpen: (id: number) => void }) {
  const { t, lang } = useLang();
  const categories = useCategories();
  const districts = useDistricts();
  const setLocation = useSetLocation();

  const [radius, setRadius] = useState(3000);
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [sort, setSort] = useState<FeedSort>("new");
  const [typed, setTyped] = useState("");
  const [search, setSearch] = useState<string | null>(null);
  const [gps, setGps] = useState<Coordinates | null>(null);
  const [gpsNote, setGpsNote] = useState<string | null>(null);

  // Qidiruvni 2 belgidan boshlaymiz (backend minimum) va bosib yubormaymiz.
  useEffect(() => {
    const value = typed.trim();
    const id = setTimeout(() => setSearch(value.length >= 2 ? value : null), 350);
    return () => clearTimeout(id);
  }, [typed]);

  const query = useMemo(
    () => ({
      ...defaultFeedQuery(),
      radius,
      categoryId,
      search,
      sort,
      latitude: gps?.latitude ?? null,
      longitude: gps?.longitude ?? null,
    }),
    [radius, categoryId, search, sort, gps],
  );

  const feed = useFeedPages(query);
  const items = feed.data?.pages.flatMap((page) => page.items) ?? [];
  const list = categories.data ?? [];
  const home = districts.data?.find((item) => item.id === profile.district_id);
  const nearLabel = gps
    ? t("gpsOn")
    : home
      ? lang === "uz"
        ? home.name_uz
        : home.name_ru
      : t("emptyHint");

  async function grabGps() {
    tap("medium");
    try {
      const point = await askPosition();
      setGps(point);
      setGpsNote(null);
      setLocation.mutate(point);
    } catch {
      setGpsNote(t("gpsError"));
    }
  }

  if (feed.isError) {
    return (
      <Notice
        title={t("errorLoad")}
        text={String(feed.error.message)}
        action={{ label: t("retry"), onClick: () => void feed.refetch() }}
      />
    );
  }

  return (
    <div className="screen">
      <header className="feed-head">
        <div className="feed-top">
          <h1 className="feed-title">{t("feedTitle")}</h1>
          <button type="button" className={`gps${gps ? " is-on" : ""}`} onClick={grabGps}>
            {t("gps")}
          </button>
        </div>
        <p className="note">{nearLabel}</p>
        <input
          className="search"
          type="search"
          value={typed}
          placeholder={t("searchPlaceholder")}
          onChange={(event) => setTyped(event.target.value)}
        />
        <ChipRow>
          {RADII.map((value) => (
            <Chip key={value} active={radius === value} onClick={() => setRadius(value)}>
              {value >= 1000 ? `${value / 1000} km` : `${value} m`}
            </Chip>
          ))}
          {SORTS.map((value) => (
            <Chip key={value} active={sort === value} onClick={() => setSort(value)}>
              {value === "new" ? t("sortNew") : value === "cheap" ? t("sortCheap") : t("sortExpensive")}
            </Chip>
          ))}
        </ChipRow>
        <ChipRow>
          <Chip active={categoryId === null} onClick={() => setCategoryId(null)}>
            {t("all")}
          </Chip>
          {list.map((category) => (
            <Chip
              key={category.id}
              active={categoryId === category.id}
              onClick={() => {
                tap();
                setCategoryId(category.id);
              }}
            >
              {lang === "uz" ? category.name_uz : category.name_ru}
            </Chip>
          ))}
        </ChipRow>
        {gpsNote && <p className="note">{gpsNote}</p>}
      </header>

      {feed.isPending ? (
        <Notice text={t("loading")} />
      ) : items.length === 0 ? (
        <Notice title={t("empty")} text={t("emptyHint")} />
      ) : (
        <div className="grid">
          {items.map((listing) => (
            <ListingCard key={listing.id} listing={listing} onOpen={onOpen} />
          ))}
        </div>
      )}

      {feed.hasNextPage && (
        <button
          type="button"
          className="btn btn-ghost more"
          disabled={feed.isFetchingNextPage}
          onClick={() => void feed.fetchNextPage()}
        >
          {t("loadMore")}
        </button>
      )}
    </div>
  );
}
