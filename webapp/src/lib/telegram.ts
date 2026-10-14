// Telegram Mini App SDK'si (index.html'dagi telegram-web-app.js) uchun yupqa qatlam.

interface TelegramUser {
  id: number;
  first_name?: string;
  username?: string;
  language_code?: string;
}

interface TelegramThemeParams {
  bg_color?: string;
  secondary_bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
}

interface TelegramMainButton {
  text: string;
  color?: string;
  textColor?: string;
  isVisible: boolean;
  isEnabled: boolean;
  isProgressVisible?: boolean;
  setText(text: string): void;
  show(): void;
  hide(): void;
  enable(): void;
  disable(): void;
  showProgress?(leaveActive?: boolean): void;
  hideProgress?(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: { user?: TelegramUser };
  colorScheme?: "light" | "dark";
  themeParams?: TelegramThemeParams;
  ready(): void;
  expand(): void;
  close?: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  onThemeChanged?: (cb: () => void) => void;
  offThemeChanged?: (cb: () => void) => void;
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
    notificationOccurred: (type: "error" | "success" | "warning") => void;
  };
  BackButton?: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void };
  MainButton?: TelegramMainButton;
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

/** Sarlavha va fon rangi: Telegram temasiga mos, aks holda CSS'dagi qiymatlar. */
export const BRAND_COLOR = "#ff5c39";
const BG_BY_SCHEME = { light: "#f6f6f6", dark: "#171717" } as const;

export function applyTheme(): void {
  const app = webApp();
  if (!app) return;
  const scheme = app.colorScheme ?? "light";
  document.documentElement.dataset.scheme = scheme;
  // Brauzerda SDK bor, lekin rang buyruqlari ishlamaydi (ogohlantirish chiqaradi).
  if (!inTelegram()) return;
  app.setHeaderColor?.(BRAND_COLOR);
  app.setBackgroundColor?.(app.themeParams?.bg_color ?? BG_BY_SCHEME[scheme]);
}

export function initTelegram(): void {
  const app = webApp();
  if (!app) return;
  app.ready();
  app.expand();
  applyTheme();
  // Telegram tungi/kunduzgi rejimni almashtirsa ranglar shu yerda yangilanadi.
  app.onThemeChanged?.(applyTheme);
}

export function tap(style: "light" | "medium" = "light"): void {
  webApp()?.HapticFeedback?.impactOccurred(style);
}

/** Orqaga qaytish tugmasi: Mini App'da ekranlar stek'ini suradi. */
export function onBackButton(handler: () => void, visible: boolean): () => void {
  const button = webApp()?.BackButton;
  if (!button || !inTelegram()) return () => undefined;
  if (visible) button.show();
  else button.hide();
  button.onClick(handler);
  return () => button.offClick(handler);
}

/** Pastdagi asosiy tugma faqat Telegram ichida ishlaydi — brauzerda SDK bor, lekin ko'rinmaydi. */
export const hasMainButton = (): boolean => inTelegram() && Boolean(webApp()?.MainButton);

/**
 * Telegram'ning pastdagi MainButton'i: matn, holat va bosilish.
 * Holatni faqat o'zgarganda yozadi — har render'da tugma qayta chizilmaydi.
 * Tozalash funksiyasi tugmani yashiradi va tinglovchini olib tashlaydi.
 */
export function mainButton(params: {
  text: string;
  visible: boolean;
  enabled?: boolean;
  progress?: boolean;
  onClick: () => void;
}): () => void {
  const button = webApp()?.MainButton;
  if (!button || !inTelegram()) return () => undefined;

  if (button.text !== params.text) button.setText(params.text);
  if (params.visible && !button.isVisible) button.show();
  if (!params.visible && button.isVisible) button.hide();

  const enabled = params.enabled !== false;
  if (enabled && !button.isEnabled) button.enable();
  if (!enabled && button.isEnabled) button.disable();

  if (params.progress) button.showProgress?.(false);
  else button.hideProgress?.();

  button.onClick(params.onClick);
  return () => {
    button.offClick(params.onClick);
    button.hideProgress?.();
    if (button.isVisible) button.hide();
  };
}
