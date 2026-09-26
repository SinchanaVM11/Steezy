import { searchInspiration } from "./inspiration";

const image = { uri: "file:///shirt.png", name: "shirt.png", type: "image/png" };

test("uploads an inspiration image and parses scored results", async () => {
  const fetcher = jest.fn().mockResolvedValue(
    new Response(
      JSON.stringify({
        semantics: "baseline_low_level_visual_similarity",
        query_dimension: 36,
        results: [
          {
            rank: 1,
            item: { id: "item-1" },
            retrieval: {
              score: 0.91,
              model_name: "visual-rgb-feature-baseline",
              model_version: "1",
              dimension: 36,
              source: "visual-feature-baseline",
              created_at: "2026-01-01T00:00:00Z",
            },
          },
        ],
      }),
      { status: 200 },
    ),
  );

  const result = await searchInspiration(fetcher, "http://api/", "user-1", image);

  expect(result.results[0].retrieval.score).toBe(0.91);
  expect(fetcher).toHaveBeenCalledWith(
    expect.stringContaining("/inspiration/search?top_k=10"),
    expect.objectContaining({ method: "POST", headers: { "X-User-ID": "user-1" } }),
  );
});

test("surfaces structured errors and malformed responses", async () => {
  const failed = jest.fn().mockResolvedValue(
    new Response(JSON.stringify({ error: { message: "Invalid image" } }), { status: 422 }),
  );
  await expect(searchInspiration(failed, "http://api", "user-1", image)).rejects.toThrow(
    "Invalid image",
  );

  const malformed = jest.fn().mockResolvedValue(
    new Response(JSON.stringify({ results: [] }), { status: 200 }),
  );
  await expect(searchInspiration(malformed, "http://api", "user-1", image)).rejects.toThrow(
    "expected contract",
  );
});
