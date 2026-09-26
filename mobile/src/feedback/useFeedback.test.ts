import { feedbackStateReducer } from "./useFeedback";

const response = {
  id: "feedback-1",
  user_id: "user-1",
  wardrobe_item_id: "item-1",
  action: "like" as const,
  context: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("feedback submission state", () => {
  it("transitions from idle to submitting to success", () => {
    const submitting = feedbackStateReducer(
      { status: "idle", response: null },
      { type: "submit" },
    );
    expect(submitting.status).toBe("submitting");
    expect(feedbackStateReducer(submitting, { type: "success", response })).toEqual({
      status: "success",
      response,
    });
  });

  it("preserves the last successful response on an error", () => {
    const state = { status: "success" as const, response };
    expect(feedbackStateReducer(state, { type: "error", message: "offline" })).toEqual({
      status: "error",
      response,
      message: "offline",
    });
  });
});
