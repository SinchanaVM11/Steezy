export type WardrobeItem = {
  id: string;
  user_id: string;
  category: string;
  subcategory: string | null;
  colors: string[];
  source: "user" | "imported";
  verification_status: "unverified";
  created_at: string;
  updated_at: string;
};

export type ApiError = {
  code: string;
  message: string;
  correlation_id: string;
  details: unknown;
};

export function apiErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null || !("error" in payload)) {
    return fallback;
  }
  const error = payload.error;
  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof error.message === "string"
  ) {
    return error.message;
  }
  return fallback;
}

function isWardrobeItem(value: unknown): value is WardrobeItem {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const item = value as Record<string, unknown>;
  return (
    typeof item.id === "string" &&
    typeof item.user_id === "string" &&
    typeof item.category === "string" &&
    (item.subcategory === null || typeof item.subcategory === "string") &&
    Array.isArray(item.colors) &&
    item.colors.every((color) => typeof color === "string") &&
    (item.source === "user" || item.source === "imported") &&
    item.verification_status === "unverified" &&
    typeof item.created_at === "string" &&
    typeof item.updated_at === "string"
  );
}

export function wardrobeItemsUrl(baseUrl: string, userId: string): string {
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, "");
  return `${normalizedBaseUrl}/wardrobe/items?user_id=${encodeURIComponent(userId)}`;
}

export async function fetchWardrobeItems(
  fetcher: typeof fetch,
  baseUrl: string,
  userId: string,
): Promise<WardrobeItem[]> {
  const response = await fetcher(wardrobeItemsUrl(baseUrl, userId));

  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      // Preserve the transport status when no JSON envelope is available.
    }
    throw new Error(
      apiErrorMessage(payload, `Wardrobe request failed with status ${response.status}`),
    );
  }

  const payload: unknown = await response.json();
  if (!Array.isArray(payload)) {
    throw new Error("Wardrobe response did not match the expected contract");
  }

  if (!payload.every(isWardrobeItem)) {
    throw new Error("Wardrobe response contained an invalid item");
  }

  return payload;
}
