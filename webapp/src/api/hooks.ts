// TanStack Query orqali ma'lumot olish. Backend tanlovi main.tsx'da bo'ladi.

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { httpBackend, tokenStore } from "./http";
import type { Backend, Coordinates, FeedQuery, ListingStatus, NewListing } from "./types";

let chosen: Backend = httpBackend;

export function setBackend(backend: Backend): void {
  chosen = backend;
}

export const useBackend = (): Backend => chosen;

const EMPTY_FEED: FeedQuery = {
  radius: 3000,
  categoryId: null,
  search: null,
  sort: "new",
  cursor: null,
  latitude: null,
  longitude: null,
};

export const feedKey = (query: FeedQuery) => ["feed", query] as const;

export const useCategories = () =>
  useQuery({ queryKey: ["categories"], queryFn: () => chosen.categories(), staleTime: 600_000 });

export const useDistricts = () =>
  useQuery({ queryKey: ["districts"], queryFn: () => chosen.districts(), staleTime: 86_400_000 });

export const useListing = (id: number) =>
  useQuery({ queryKey: ["listing", id], queryFn: () => chosen.listing(id) });

export const useMine = () => useQuery({ queryKey: ["mine"], queryFn: () => chosen.mine() });

export function useCreateListing() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: NewListing) => chosen.create(input),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["feed"] });
      void client.invalidateQueries({ queryKey: ["mine"] });
    },
  });
}

export function useAddImage() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ listingId, file }: { listingId: number; file: File }) =>
      chosen.addImage(listingId, file),
    onSuccess: (_data, variables) => {
      void client.invalidateQueries({ queryKey: ["listing", variables.listingId] });
      void client.invalidateQueries({ queryKey: ["feed"] });
    },
  });
}

export function useSetStatus() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: ListingStatus }) =>
      chosen.setStatus(id, status),
    onSuccess: (listing) => {
      void client.invalidateQueries({ queryKey: ["mine"] });
      void client.invalidateQueries({ queryKey: ["feed"] });
      void client.invalidateQueries({ queryKey: ["listing", listing.id] });
    },
  });
}

export function useSetLocation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (coords: Coordinates) => chosen.setLocation(coords),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["feed"] });
      void client.invalidateQueries({ queryKey: ["session"] });
    },
  });
}

export const defaultFeedQuery = (): FeedQuery => ({ ...EMPTY_FEED });

/** Lenta sahifa-sahifa bilan: cursor keyset pagination (backend'dagi next_cursor). */
export function useFeedPages(query: FeedQuery) {
  return useInfiniteQuery({
    queryKey: feedKey(query),
    queryFn: ({ pageParam }) => chosen.feed({ ...query, cursor: pageParam }),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
    placeholderData: (previous) => previous,
  });
}

/** Sessiya: token bo'lsa profilni, bo'lmasa initData bilan kirishni so'raydi. */
export function useSession(initData: string) {
  return useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      if (tokenStore.read()) {
        try {
          return await chosen.profile();
        } catch {
          tokenStore.clear();
        }
      }
      return chosen.login(initData);
    },
    staleTime: 3_600_000,
    retry: false,
  });
}
