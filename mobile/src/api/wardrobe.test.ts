import { fetchWardrobeItems, wardrobeItemsUrl } from "./wardrobe";

describe("wardrobe API client", () => {
  it("builds a user-scoped collection URL", () => {
    expect(wardrobeItemsUrl("http://localhost:8000/", "user/1")).toBe(
      "http://localhost:8000/wardrobe/items?user_id=user%2F1",
    );
  });

  it("fetches a typed wardrobe collection", async () => {
    const item = {
      id: "item-1",
      user_id: "user-1",
      category: "shirt",
      subcategory: null,
      colors: ["navy"],
      source: "user",
      verification_status: "unverified",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };
    const fetcher = jest.fn(async () => new Response(JSON.stringify([item]), { status: 200 }));

    await expect(fetchWardrobeItems(fetcher, "http://localhost:8000", "user-1")).resolves.toEqual([
      item,
    ]);
  });

  it("rejects an item that does not match the contract", async () => {
    const fetcher = jest.fn(async () => new Response(JSON.stringify([{ category: "shirt" }]), { status: 200 }));

    await expect(fetchWardrobeItems(fetcher, "http://localhost:8000", "user-1")).rejects.toThrow(
      "invalid item",
    );
  });
});
