// Raqam va masofani odam tilida ko'rsatish.

const THOUSAND = /(\d)(?=(\d{3})+$)/g;

export function formatSum(value: number): string {
  return value.toString().replace(THOUSAND, "$1 ");
}

export function formatPrice(price: number, priceType: string, labels: {
  free: string;
  negotiable: string;
}): string {
  if (priceType === "free") return labels.free;
  const base = formatSum(price);
  return priceType === "negotiable" ? `${base} · ${labels.negotiable}` : `${base} so'm`;
}

/** Karrot uslubidagi masofa: "400 m", "1,2 km". */
export function formatDistance(meters: number | null): string | null {
  if (meters === null) return null;
  if (meters < 1000) return `${Math.round(meters)} m`;
  const km = meters / 1000;
  return `${km.toFixed(1).replace(".", ",")} km`;
}
