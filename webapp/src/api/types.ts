// Backend javoblariga mos turlar (app/modules/*/schemas.py).

export type PriceType = "fixed" | "negotiable" | "free";
export type Condition = "new" | "used";
export type ListingStatus = "active" | "reserved" | "sold" | "hidden";
export type FeedSort = "new" | "cheap" | "expensive";

export interface ListingImage {
  id: number;
  storage_key: string;
  width: number | null;
  height: number | null;
  position: number;
  url: string;
  thumb_url: string;
}

export interface Listing {
  id: number;
  seller_id: number;
  category_id: number;
  title: string;
  description: string;
  price: number;
  price_type: string;
  condition: string;
  status: string;
  district_id: number | null;
  view_count: number;
  images: ListingImage[];
  distance_m: number | null;
}

export interface FeedPage {
  items: Listing[];
  next_cursor: string | null;
}

export interface Category {
  id: number;
  slug: string;
  name_uz: string;
  name_ru: string;
}

export interface District {
  id: number;
  name_uz: string;
  name_ru: string;
  latitude: number;
  longitude: number;
}

export interface Profile {
  id: number;
  display_name: string;
  username: string | null;
  language: string;
  district_id: number | null;
  trust_score: number;
  role: string;
  has_phone: boolean;
}

export interface FeedQuery {
  radius: number;
  categoryId: number | null;
  search: string | null;
  sort: FeedSort;
  cursor: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface NewListing {
  title: string;
  description: string;
  price: number;
  priceType: PriceType;
  condition: Condition;
  categoryId: number;
  latitude: number | null;
  longitude: number | null;
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

/** Ilovaning backend bilan chegarasi — HTTP implentatsiya va test uchun mock. */
export interface Backend {
  login(initData: string): Promise<Profile>;
  profile(): Promise<Profile>;
  categories(): Promise<Category[]>;
  districts(): Promise<District[]>;
  feed(query: FeedQuery): Promise<FeedPage>;
  listing(id: number): Promise<Listing>;
  mine(): Promise<Listing[]>;
  create(input: NewListing): Promise<Listing>;
  addImage(listingId: number, file: File): Promise<ListingImage>;
  setStatus(id: number, status: ListingStatus): Promise<Listing>;
  setLocation(coords: Coordinates): Promise<Profile>;
}
