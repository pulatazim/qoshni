// Telegram Mini App SDK'si (index.html'dagi telegram-web-app.js) uchun yupqa qatlam.

interface TelegramUser {
  id: number;
  first_name?: string;
  username?: string;
  language_code?: string;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: { user?: TelegramUser };
  colorScheme?: "light" | "dark";
  ready(): void;
  expand(): void;
  close?: () => void;
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
    notificationOccurred: (type: "error" | "success" | "warning") => void;
  };
  BackButton?: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void };
  showPopup?: (params: { title?: string; message?: string; buttons?: unknown[] }) => void;
  openTelegramLink?: (url: string) => void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export const webApp = (): TelegramWebApp | null => window.Telegram?.WebApp ?? null;

export const inTelegram = (): boolean => Boolean(webApp()?.initData);

/** Backend'ga yuboriladigan imzolangan satr; Telegram tashqarisida demo qiymat. */
export const initDataString = (): string => webApp()?.initData || "demo_init_data_for_browser_only";

/** Telegram brauzerda ochilganda (Mini App'siz) ko'rinadigan holat: mock ma'lumot.
 * `?live=1` bilan brauzerdan haqiqiy backend'ga ulanib sinash mumkin (faqat DEV). */
export const shouldUseMock = (): boolean =>
  import.meta.env.DEV && !inTelegram() && new URLSearchParams(location.search).get("live") !== "1";

export const telegramLanguage = (): "uz" | "ru" =>
  webApp()?.initDataUnsafe?.user?.language_code?.startsWith("ru") ? "ru" : "uz";

export function initTelegram(): void {
  const app = webApp();
  if (!app) return;
  app.ready();
  app.expand();
  document.documentElement.dataset.scheme = app.colorScheme ?? "light";
}

export function tap(style: "light" | "medium" = "light"): void {
  webApp()?.HapticFeedback?.impactOccurred(style);
}

/** Orqaga qaytish tugmasi: Mini App'da ekranlar stek'ini suradi. */
export function onBackButton(handler: () => void, visible: boolean): () => void {
  const button = webApp()?.BackButton;
  if (!button) return () => undefined;
  if (visible) button.show();
  else button.hide();
  button.onClick(handler);
  return () => button.offClick(handler);
}
