// Holat va holat-matnlarini bitta joydan tarjima qilish.

import type { T } from "./i18n";

export const conditionLabel = (condition: string, t: T): string =>
  condition === "new" ? t("conditionNew") : t("conditionUsed");

export function statusLabel(status: string, t: T): string {
  if (status === "sold") return t("sold");
  if (status === "reserved") return t("reserved");
  if (status === "hidden") return t("hidden");
  return t("active");
}
