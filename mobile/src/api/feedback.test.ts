import { submitFeedback } from "./feedback";

describe("feedback API client", () => {
  const response = {
    id: "feedback-1",
    user_id: "user-1",
    wardrobe_item_id: "item-1",
    action: "like" as const,
    context: null,
    created_at: "2026-01-01T00:00:00Z",
  };

  it("submits an allowed action and validates the response", async () => {
    const fetcher = jest.fn(async () => new Response(JSON.stringify(response), { status: 201 }));

    await expect(
      submitFeedback(fetcher, "http://localhost:8000/", "user-1", "item-1", "like"),
    ).resolves.toEqual(response);
    expect(fetcher).toHaveBeenCalledWith("http://localhost:8000/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "user-1",
        wardrobe_item_id: "item-1",
        action: "like",
        context: null,
      }),
    });
  });

  it("rejects HTTP failures and malformed responses", async () => {
    const failed = jest.fn(async () =>
      new Response(
        JSON.stringify({
          error: {
            code: "item_not_owned",
            message: "wardrobe item is not owned by user",
            correlation_id: "request-1",
            details: null,
          },
        }),
        { status: 404 },
      ),
    );
    await expect(
      submitFeedback(failed, "http://localhost:8000", "user-1", "item-1", "like"),
    ).rejects.toThrow("not owned");

    const malformed = jest.fn(async () => new Response(JSON.stringify({ id: "missing" }), { status: 201 }));
    await expect(
      submitFeedback(malformed, "http://localhost:8000", "user-1", "item-1", "like"),
    ).rejects.toThrow("expected contract");
  });
});
