// Ikki tilli matnlar: foydalanuvchi Telegram tiliga qarab uz yoki ru.

import { createContext, useContext } from "react";

const STRINGS = {
  feedTitle: { uz: "Yaqin atrofdagilar", ru: "Рядом с вами" },
  all: { uz: "Barchasi", ru: "Все" },
  searchPlaceholder: { uz: "Qidirish", ru: "Поиск" },
  empty: { uz: "Bu yerda hozircha e'lon yo'q", ru: "Пока нет объявлений рядом" },
  emptyHint: {
    uz: "Radiusni kengaytiring yoki keyinroq qayla ko'ring",
    ru: "Увеличьте радиус или загляните позже",
  },
  sell: { uz: "Sotish", ru: "Продать" },
  tabFeed: { uz: "Lenta", ru: "Лента" },
  tabMine: { uz: "Mening", ru: "Мои" },
  mine: { uz: "Mening e'lonlarim", ru: "Мои объявления" },
  profile: { uz: "Profil", ru: "Профиль" },
  notifications: { uz: "Bildirishnoma", ru: "Уведомления" },
  soon: { uz: "Tez orada", ru: "Скоро" },
  free: { uz: "Bepul", ru: "Бесплатно" },
  negotiable: { uz: "Kelishamiz", ru: "Торг" },
  conditionNew: { uz: "Yangi", ru: "Новое" },
  conditionUsed: { uz: "Ishlatilgan", ru: "Б/у" },
  sold: { uz: "Sotildi", ru: "Продано" },
  reserved: { uz: "Band", ru: "Занято" },
  active: { uz: "Faol", ru: "Активно" },
  hidden: { uz: "Yashirin", ru: "Скрыто" },
  writeSeller: { uz: "Sotuvchiga yozish", ru: "Написать продавцу" },
  neighbor: { uz: "Qo'shni", ru: "Сосед" },
  chatSoon: {
    uz: "Bot orqali yozish keyingi haftada qo'shiladi",
    ru: "Чат через бота появится на следующей неделе",
  },
  createTitle: { uz: "E'lon qo'shish", ru: "Добавить объявление" },
  titleLabel: { uz: "Nima sotmoqchisiz?", ru: "Что вы продаёте?" },
  descriptionLabel: { uz: "Tavsif", ru: "Описание" },
  priceLabel: { uz: "Narx, so'm", ru: "Цена, сум" },
  categoryLabel: { uz: "Kategoriya", ru: "Категория" },
  conditionLabel: { uz: "Holati", ru: "Состояние" },
  priceFixed: { uz: "Aniq narx", ru: "Точная цена" },
  titleTooShort: {
    uz: "Sarlavha kamida 3 ta belgi",
    ru: "Заголовок минимум 3 символа",
  },
  categoryRequired: {
    uz: "Kategoriyani tanlang",
    ru: "Выберите категорию",
  },
  photoLabel: { uz: "Rasm (1 ta, keyin ko'paytiralamiz)", ru: "Фото (1 шт.)" },
  locationLabel: { uz: "Joylashuv", ru: "Расположение" },
  homeDistrict: { uz: "Hudud", ru: "Район" },
  languageLabel: { uz: "Til", ru: "Язык" },
  useGps: { uz: "GPS'ni yuborish", ru: "Отправить GPS" },
  useProfile: { uz: "Profdagi joylashuv", ru: "Из профиля" },
  useProfileHint: {
    uz: "Profpdagi saqlangan joylashuv ishlatiladi",
    ru: "Будет использован адрес из профиля",
  },
  publish: { uz: "Joylash", ru: "Опубликовать" },
  published: { uz: "E'lon qo'shildi", ru: "Объявление добавлено" },
  trust: { uz: "Ishonch", ru: "Доверие" },
  views: { uz: "Ko'rish", ru: "Просмотры" },
  back: { uz: "Orqaga", ru: "Назад" },
  loading: { uz: "Yuklanmoqda…", ru: "Загрузка…" },
  errorLoad: { uz: "Olb bo'lmadi", ru: "Не удалось загрузить" },
  retry: { uz: "Qayta urinish", ru: "Повторить" },
  radius: { uz: "Radius", ru: "Радиус" },
  gps: { uz: "GPS", ru: "GPS" },
  gpsOn: { uz: "GPS bo'yicha", ru: "По GPS" },
  gpsError: {
    uz: "Joylashuvni ola tmadim, tuman bo'yicha ko'rsatyapti",
    ru: "Геолокация недоступна, показываем по району",
  },
  loadMore: { uz: "Ko'proq", ru: "Ещё" },
  sortNew: { uz: "Yangi", ru: "Новые" },
  sortCheap: { uz: "Arzon", ru: "Дешёвые" },
  sortExpensive: { uz: "Qimmat", ru: "Дорогие" },
  noPhoto: { uz: "Rasm yo'q", ru: "Нет фото" },
  removePhoto: { uz: "Ochirish", ru: "Удалить" },
  saveDraft: { uz: "Saqlanmoqda…", ru: "Сохраняю…" },
  mockBanner: {
    uz: "Demo rejim: Telegram ichida emaslang (soxta ma'lumot)",
    ru: "Демо-режим: данные примерные",
  },
} as const;

export type Key = keyof typeof STRINGS;

export function makeT(language: "uz" | "ru") {
  return (key: Key): string => STRINGS[key][language];
}

export type T = ReturnType<typeof makeT>;

export interface Lang {
  lang: "uz" | "ru";
  t: T;
}

export const LangContext = createContext<Lang>({ lang: "uz", t: makeT("uz") });

export const useLang = (): Lang => useContext(LangContext);
