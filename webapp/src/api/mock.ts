// Demo rejim: Telegram tashqarisida (brauzerda) interfeysni ko'rish uchun.
// Faqat DEV'da yuklanadi — ishlab chiqarish bunday kodga tushmaydi.

import type {
  Backend,
  Category,
  Coordinates,
  District,
  FeedPage,
  FeedQuery,
  Listing,
  ListingImage,
  ListingStatus,
  NewListing,
  Profile,
} from "./types";

function photo(color: string, label: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
    <rect width="400" height="400" fill="${color}"/>
    <text x="200" y="210" font-family="sans-serif" font-size="34" fill="#ffffff"
      text-anchor="middle">${label}</text></svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

const CATEGORIES: Category[] = [
  { id: 1, slug: "kitob", name_uz: "Kitoblar", name_ru: "Книги" },
  { id: 2, slug: "mebel", name_uz: "Mebellar", name_ru: "Мебель" },
  { id: 3, slug: "elektronika", name_uz: "Elektronika", name_ru: "Электроника" },
  { id: 4, slug: "kiyim", name_uz: "Kiyim-kechak", name_ru: "Одежда" },
  { id: 5, slug: "bolalar", name_uz: "Bolalar tovarlari", name_ru: "Детские товары" },
  { id: 6, slug: "transport", name_uz: "Transport", name_ru: "Транспорт" },
];

const DISTRICTS: District[] = [
  { id: 1, name_uz: "Chilonzor", name_ru: "Чиланзар", latitude: 41.2805, longitude: 69.2268 },
  { id: 2, name_uz: "Mirzo Ulug'bek", name_ru: "Мирзо Улуғбек", latitude: 41.3125, longitude: 69.28 },
  { id: 3, name_uz: "Yakkasaroy", name_ru: "Яккасарой", latitude: 41.3031, longitude: 69.2783 },
];

function image(id: number, color: string, label: string): ListingImage {
  const url = photo(color, label);
  return { id, storage_key: `demo/${id}.webp`, width: 400, height: 400, position: 0, url, thumb_url: url };
}

let sequence = 100;

const LISTINGS: Listing[] = [
  {
    id: 1, seller_id: 7, category_id: 1, title: "Sardor Abduhalimov she'riy to'plami",
    description: "1972 yil nashri, holati yaxshi. Mahalladoshlarga chegirma.",
    price: 45_000, price_type: "fixed", condition: "used", status: "active",
    district_id: 2, view_count: 12, images: [image(1, "#8b5cf6", "Kitob")], distance_m: 320,
  },
  {
    id: 2, seller_id: 8, category_id: 2, title: "Yong'oq stol, 4 oyoqli",
    description: "Hatoqlangan, o'z qo'limda yasaganman. Olib ketishga yordam beraman.",
    price: 850_000, price_type: "negotiable", condition: "used", status: "active",
    district_id: 2, view_count: 40, images: [image(2, "#0ea5e9", "Stol")], distance_m: 780,
  },
  {
    id: 3, seller_id: 9, category_id: 3, title: "iPhone 12, 128 GB",
    description: "Batareya 89%, qutisi va kabeli bilan.",
    price: 5_200_000, price_type: "fixed", condition: "used", status: "active",
    district_id: 3, view_count: 214, images: [image(3, "#111827", "Telefon")], distance_m: 1_450,
  },
  {
    id: 4, seller_id: 7, category_id: 5, title: "Bolalar velosipedi 3-6 yosh",
    description: "Bir mavsum ishlatilgan, chiqib ketgan joyi yo'q.",
    price: 0, price_type: "free", condition: "used", status: "active",
    district_id: 2, view_count: 66, images: [image(4, "#f59e0b", "Velosiped")], distance_m: 240,
  },
  {
    id: 5, seller_id: 10, category_id: 4, title: "Qishki kurtka, M razmer",
    description: "Yangi, yorliqda. Og'irlikni o'lchab ko'rmadim.",
    price: 320_000, price_type: "fixed", condition: "new", status: "reserved",
    district_id: 1, view_count: 8, images: [image(5, "#ef4444", "Kurtka")], distance_m: 2_600,
  },
  {
    id: 6, seller_id: 8, category_id: 6, title: "Damas, 2019 yil",
    description: "Yurish 68 ming km, bir xojadan. Hujjatlari to'liq.",
    price: 61_000_000, price_type: "negotiable", condition: "used", status: "active",
    district_id: 1, view_count: 512, images: [image(6, "#22c55e", "Damas")], distance_m: 3_100,
  },
];

const ME: Profile = {
  id: 7,
  display_name: "Dilnoza",
  username: "dilnoza_q",
  language: "uz",
  district_id: 2,
  trust_score: 62,
  role: "user",
  has_phone: true,
};

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockBackend: Backend = {
  async login() {
    await delay(200);
    return ME;
  },
  profile: async () => ME,
  categories: async () => CATEGORIES,
  districts: async () => DISTRICTS,

  async feed(query: FeedQuery): Promise<FeedPage> {
    await delay(250);
    const items = LISTINGS.filter(
      (item) =>
        item.status === "active" &&
        (query.categoryId === null || item.category_id === query.categoryId) &&
        item.distance_m !== null &&
        item.distance_m <= query.radius &&
        (query.search === null ||
          item.title.toLowerCase().includes(query.search.toLowerCase()) ||
          item.description.toLowerCase().includes(query.search.toLowerCase())),
    );
    const sorted = [...items].sort((a, b) =>
      query.sort === "cheap" ? a.price - b.price : query.sort === "expensive" ? b.price - a.price : b.id - a.id,
    );
    return { items: sorted, next_cursor: null };
  },

  async listing(id) {
    await delay(150);
    const found = LISTINGS.find((item) => item.id === id);
    if (!found) throw new Error("demo rejimida bunday e'lon yo'q");
    return found;
  },

  async mine() {
    await delay(150);
    return LISTINGS.filter((item) => item.seller_id === ME.id);
  },

  async create(input: NewListing) {
    await delay(300);
    sequence += 1;
    const created: Listing = {
      id: sequence,
      seller_id: ME.id,
      category_id: input.categoryId,
      title: input.title,
      description: input.description,
      price: input.price,
      price_type: input.priceType,
      condition: input.condition,
      status: "active",
      district_id: ME.district_id,
      view_count: 0,
      images: [],
      distance_m: 150,
    };
    LISTINGS.unshift(created);
    return created;
  },

  async addImage(listingId, file) {
    const url = URL.createObjectURL(file);
    const created = LISTINGS.find((item) => item.id === listingId);
    const added = {
      id: sequence + 1,
      storage_key: `demo/${listingId}.webp`,
      width: 400,
      height: 400,
      position: 0,
      url,
      thumb_url: url,
    };
    if (created) created.images = [added];
    return added;
  },

  async setStatus(id, status: ListingStatus) {
    const item = LISTINGS.find((listing) => listing.id === id);
    if (item) item.status = status;
    if (!item) throw new Error("demo rejimida bunday e'lon yo'q");
    return item;
  },

  setLocation: async (_coords: Coordinates) => ME,
};
