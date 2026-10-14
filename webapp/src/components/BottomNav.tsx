// Karrot uslubidagi pastki panel: 3 bo'lim + markazda to'q sariq "Sotish" tugmasi.

import { useLang } from "../lib/i18n";
import { tap } from "../lib/telegram";

export type Tab = "feed" | "mine" | "profile";

const ICONS: Record<Tab, string> = {
  feed: "M3 10.5 12 3l9 7.5V21h-6v-6h-6v6H3z",
  mine: "M4 6h16M4 12h16M4 18h10",
  profile: "M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm-8 9a8 8 0 0 1 16 0",
};

function Icon({ path }: { path: string }) {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
      <path d={path} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  );
}

export function BottomNav({
  active,
  onTab,
  onSell,
}: {
  active: Tab | null;
  onTab: (tab: Tab) => void;
  onSell: () => void;
}) {
  const { t } = useLang();

  const sell = () => {
    tap("medium");
    onSell();
  };

  return (
    <nav className="tabbar">
      <TabButton label={t("tabFeed")} tab="feed" active={active === "feed"} onClick={() => onTab("feed")} />
      <TabButton label={t("tabMine")} tab="mine" active={active === "mine"} onClick={() => onTab("mine")} />
      <button type="button" className="sell" onClick={sell}>
        <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
          <path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
        </svg>
        <span className="sell-label">{t("sell")}</span>
      </button>
      <TabButton
        label={t("profile")}
        tab="profile"
        active={active === "profile"}
        onClick={() => onTab("profile")}
      />
    </nav>
  );
}

function TabButton({
  label,
  tab,
  active,
  onClick,
}: {
  label: string;
  tab: Tab;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button type="button" className={`tab${active ? " is-active" : ""}`} onClick={onClick}>
      <Icon path={ICONS[tab]} />
      <span>{label}</span>
    </button>
  );
}
