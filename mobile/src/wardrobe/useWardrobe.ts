import { useCallback, useEffect, useState } from "react";

import { fetchWardrobeItems, WardrobeItem } from "../api/wardrobe";

export type WardrobeState =
  | { status: "idle"; items: WardrobeItem[] }
  | { status: "loading"; items: WardrobeItem[] }
  | { status: "success"; items: WardrobeItem[] }
  | { status: "empty"; items: [] }
  | { status: "error"; items: WardrobeItem[]; message: string };

export function wardrobeStateReducer(
  state: WardrobeState,
  action:
    | { type: "load" }
    | { type: "success"; items: WardrobeItem[] }
    | { type: "error"; message: string },
): WardrobeState {
  switch (action.type) {
    case "load":
      return { status: "loading", items: state.items };
    case "success":
      return action.items.length === 0
        ? { status: "empty", items: [] }
        : { status: "success", items: action.items };
    case "error":
      return { status: "error", items: state.items, message: action.message };
  }
}

export function useWardrobe(userId: string, baseUrl: string) {
  const [state, setState] = useState<WardrobeState>({ status: "idle", items: [] });

  const load = useCallback(async () => {
    if (!userId.trim()) {
      setState({
        status: "error",
        items: [],
        message: "Configure a user ID before loading the wardrobe.",
      });
      return;
    }

    setState((current) => wardrobeStateReducer(current, { type: "load" }));
    try {
      const items = await fetchWardrobeItems(fetch, baseUrl, userId);
      setState((current) => wardrobeStateReducer(current, { type: "success", items }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to load wardrobe.";
      setState((current) => wardrobeStateReducer(current, { type: "error", message }));
    }
  }, [baseUrl, userId]);

  useEffect(() => {
    void load();
  }, [load]);

  return { state, reload: load };
}
