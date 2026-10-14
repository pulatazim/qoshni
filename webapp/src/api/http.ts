// HTTP backend: barcha so'rovlar /api/v1 orqali, JWT bu yerda qo'shiladi.

import type {
  Backend,
  Category,
  Coordinates,
  District,
  FeedPage,
  Listing,
  ListingImage,
  ListingStatus,
  Profile,
} from "./types";

const TOKEN_KEY = "qoshni.token";

export const tokenStore = {
  read: (): string | null => sessionStorage.getItem(TOKEN_KEY),
  write: (token: string): void => sessionStorage.setItem(TOKEN_KEY, token),
  clear: (): void => sessionStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
    readonly retryAfter: number | null,
  ) {
    super(message);
  }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = tokenStore.read();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`/api/v1${path}`, { ...init, headers });
  if (!response.ok) {
    let code = "internal_error";
    let message = "Xato yuz berdi";
    try {
      const body = (await response.json()) as { error?: { code?: string; message?: string } };
      code = body.error?.code ?? code;
      message = body.error?.message ?? message;
    } catch {
      // javob JSON bo'lmasa shu soya xato bilan qaytamiz
    }
    throw new ApiError(
      code,
      message,
      response.status,
      Number(response.headers.get("retry-after")) || null,
    );
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

interface TokenResponse {
  access_token: string;
  user: Profile;
}

export const httpBackend: Backend = {
  async login(initData) {
    const data = await call<TokenResponse>("/auth/telegram", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    });
    tokenStore.write(data.access_token);
    return data.user;
  },

  profile: () => call<Profile>("/me"),
  categories: () => call<Category[]>("/categories"),
  districts: () => call<District[]>("/districts"),

  feed(query) {
    const params = new URLSearchParams({ limit: "20", radius: String(query.radius) });
    if (query.categoryId !== null) params.set("category", String(query.categoryId));
    if (query.search) params.set("q", query.search);
    if (query.sort !== "new") params.set("sort", query.sort);
    if (query.cursor) params.set("cursor", query.cursor);
    if (query.latitude !== null && query.longitude !== null) {
      params.set("latitude", String(query.latitude));
      params.set("longitude", String(query.longitude));
    }
    return call<FeedPage>(`/listings?${params.toString()}`);
  },

  listing: (id) => call<Listing>(`/listings/${id}`),
  mine: async () => (await call<FeedPage>("/listings/mine?limit=50")).items,

  create(input) {
    return call<Listing>("/listings", {
      method: "POST",
      body: JSON.stringify({
        title: input.title,
        description: input.description,
        price: input.price,
        price_type: input.priceType,
        condition: input.condition,
        category_id: input.categoryId,
        latitude: input.latitude,
        longitude: input.longitude,
      }),
    });
  },

  addImage(listingId, file) {
    const body = new FormData();
    body.append("file", file);
    return call<ListingImage>(`/listings/${listingId}/images`, { method: "POST", body });
  },

  setStatus(id, status: ListingStatus) {
    return call<Listing>(`/listings/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
  },

  setLocation(coords: Coordinates) {
    return call<Profile>("/me/location", { method: "PUT", body: JSON.stringify(coords) });
  },
};
