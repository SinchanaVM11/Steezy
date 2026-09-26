import { wardrobeStateReducer, WardrobeState } from "./useWardrobe";

const item = {
  id: "item-1",
  user_id: "user-1",
  category: "shirt",
  subcategory: null,
  colors: ["navy"],
  source: "user" as const,
  verification_status: "unverified" as const,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("wardrobe state transitions", () => {
  it("moves through loading to success", () => {
    const loading = wardrobeStateReducer(
      { status: "idle", items: [] },
      { type: "load" },
    );

    expect(loading.status).toBe("loading");
    expect(wardrobeStateReducer(loading, { type: "success", items: [item] })).toEqual({
      status: "success",
      items: [item],
    });
  });

  it("represents an empty wardrobe separately", () => {
    const state: WardrobeState = { status: "loading", items: [] };

    expect(wardrobeStateReducer(state, { type: "success", items: [] })).toEqual({
      status: "empty",
      items: [],
    });
  });

  it("keeps previously loaded items visible when a reload fails", () => {
    const state: WardrobeState = { status: "success", items: [item] };

    expect(wardrobeStateReducer(state, { type: "error", message: "503" })).toEqual({
      status: "error",
      items: [item],
      message: "503",
    });
  });
});
