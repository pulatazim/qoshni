// Qo'shni Mini App: ekran stek'i bilan oddiy navigatsiya (router kutubxonasiz).

import { useEffect, useMemo, useState } from "react";
import { useSession } from "./api/hooks";
import { ApiError } from "./api/http";
import { BottomNav, type Tab } from "./components/BottomNav";
import { Notice } from "./components/States";
import { Create } from "./screens/Create";
import { Feed } from "./screens/Feed";
import { ListingView } from "./screens/ListingView";
import { Mine } from "./screens/Mine";
import { Profile } from "./screens/Profile";
import { LangContext, makeT } from "./lib/i18n";
import { initDataString, onBackButton, shouldUseMock, telegramLanguage } from "./lib/telegram";

export type Route =
  | { name: "feed" }
  | { name: "listing"; id: number }
  | { name: "create" }
  | { name: "mine" }
  | { name: "profile" };

const TAB_OF: Record<Tab, Route> = {
  feed: { name: "feed" },
  mine: { name: "mine" },
  profile: { name: "profile" },
};

export function App() {
  const [stack, setStack] = useState<Route[]>([{ name: "feed" }]);
  const route = stack[stack.length - 1];

  const [initData] = useState(initDataString);
  const session = useSession(initData);
  const profile = session.data;

  const lang = useMemo(() => {
    const value = profile?.language === "ru" ? "ru" : telegramLanguage();
    return { lang: value, t: makeT(value) };
  }, [profile?.language]);
  const { t } = lang;

  const open = (next: Route) => setStack((current) => [...current, next]);
  const pop = () => setStack((current) => (current.length > 1 ? current.slice(0, -1) : current));
  const goTab = (tab: Tab) => setStack([TAB_OF[tab]]);

  // Telegram'ning "Orqaga" tugmasi stek'dan bitta ekran chiqaradi.
  useEffect(() => onBackButton(pop, stack.length > 1), [stack.length]);

  if (!profile) {
    if (session.isError) {
      // Backend javob bergan bo'lsa uning xabari, bo'lmasa umumiy maslahat ko'rsatiladi.
      const reachedApi = session.error instanceof ApiError;
      return (
        <Notice
          title={t("errorLoad")}
          text={
            reachedApi
              ? String(session.error.message)
              : "Mini App Telegram boti ichida ishlaydi. 'Qo'shni' tugmasidan kiring."
          }
          action={{ label: t("retry"), onClick: () => void session.refetch() }}
        />
      );
    }
    return <Notice text={t("loading")} />;
  }

  return (
    <LangContext.Provider value={lang}>
      <div className="app">
        {shouldUseMock() && <div className="demo-banner">{t("mockBanner")}</div>}
        {route.name === "feed" && <Feed profile={profile} onOpen={(id) => open({ name: "listing", id })} />}
        {route.name === "listing" && <ListingView id={route.id} me={profile} onBack={pop} />}
        {route.name === "create" && <Create onBack={pop} onDone={(id) => setStack([{ name: "listing", id }])} />}
        {route.name === "mine" && (
          <Mine onOpen={(id) => open({ name: "listing", id })} onSell={() => open({ name: "create" })} />
        )}
        {route.name === "profile" && <Profile profile={profile} onMyListings={() => goTab("mine")} />}
        <BottomNav
          active={route.name === "listing" || route.name === "create" ? null : route.name}
          onTab={goTab}
          onSell={() => open({ name: "create" })}
        />
      </div>
    </LangContext.Provider>
  );
}
