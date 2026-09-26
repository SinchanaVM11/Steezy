import { apiErrorMessage, WardrobeItem } from "./wardrobe";

export type InspirationResult = {
  rank: number;
  item: WardrobeItem;
  retrieval: {
    score: number;
    model_name: string;
    model_version: string;
    dimension: number;
    source: string;
    created_at: string;
  };
};

export type InspirationResponse = {
  semantics: "baseline_low_level_visual_similarity";
  query_dimension: number;
  results: InspirationResult[];
};

function isResponse(value: unknown): value is InspirationResponse {
  if (typeof value !== "object" || value === null) return false;
  const payload = value as Record<string, unknown>;
  return (
    payload.semantics === "baseline_low_level_visual_similarity" &&
    typeof payload.query_dimension === "number" &&
    Array.isArray(payload.results) &&
    payload.results.every((result) => {
      if (typeof result !== "object" || result === null) return false;
      const entry = result as Record<string, unknown>;
      const retrieval = entry.retrieval as Record<string, unknown> | undefined;
      return (
        typeof entry.rank === "number" &&
        typeof entry.item === "object" &&
        retrieval !== undefined &&
        typeof retrieval.score === "number" &&
        typeof retrieval.model_name === "string" &&
        typeof retrieval.model_version === "string" &&
        typeof retrieval.dimension === "number" &&
        typeof retrieval.source === "string"
      );
    })
  );
}

export function inspirationSearchUrl(baseUrl: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/inspiration/search`;
}

export async function searchInspiration(
  fetcher: typeof fetch,
  baseUrl: string,
  userId: string,
  image: { uri: string; name: string; type: string },
  options: { topK?: number; threshold?: number } = {},
): Promise<InspirationResponse> {
  const form = new FormData();
  form.append("file", {
    uri: image.uri,
    name: image.name,
    type: image.type,
  } as unknown as Blob);
  const params = new URLSearchParams({
    top_k: String(options.topK ?? 10),
    similarity_threshold: String(options.threshold ?? 0),
  });
  const response = await fetcher(`${inspirationSearchUrl(baseUrl)}?${params}`, {
    method: "POST",
    headers: { "X-User-ID": userId },
    body: form,
  });
  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      // Preserve transport status when no structured envelope is available.
    }
    throw new Error(
      apiErrorMessage(payload, `Inspiration request failed with status ${response.status}`),
    );
  }
  const payload: unknown = await response.json();
  if (!isResponse(payload)) {
    throw new Error("Inspiration response did not match the expected contract");
  }
  return payload;
}
