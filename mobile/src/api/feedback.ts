export const FEEDBACK_ACTIONS = [
  "like",
  "dislike",
  "save",
  "skip",
  "wear",
  "not_relevant",
] as const;

export type FeedbackAction = (typeof FEEDBACK_ACTIONS)[number];

export type FeedbackResponse = {
  id: string;
  user_id: string;
  wardrobe_item_id: string;
  action: FeedbackAction;
  context: string | null;
  created_at: string;
};

function apiErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null || !("error" in payload)) {
    return fallback;
  }
  const error = payload.error;
  return typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof error.message === "string"
    ? error.message
    : fallback;
}

export function feedbackUrl(baseUrl: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/feedback`;
}

function isFeedbackAction(value: unknown): value is FeedbackAction {
  return typeof value === "string" && FEEDBACK_ACTIONS.includes(value as FeedbackAction);
}

function isFeedbackResponse(value: unknown): value is FeedbackResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const response = value as Record<string, unknown>;
  return (
    typeof response.id === "string" &&
    typeof response.user_id === "string" &&
    typeof response.wardrobe_item_id === "string" &&
    isFeedbackAction(response.action) &&
    (response.context === null || typeof response.context === "string") &&
    typeof response.created_at === "string"
  );
}

export async function submitFeedback(
  fetcher: typeof fetch,
  baseUrl: string,
  userId: string,
  wardrobeItemId: string,
  action: FeedbackAction,
  context: string | null = null,
): Promise<FeedbackResponse> {
  const response = await fetcher(feedbackUrl(baseUrl), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      wardrobe_item_id: wardrobeItemId,
      action,
      context,
    }),
  });

  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      // Preserve the transport status when no JSON envelope is available.
    }
    throw new Error(
      apiErrorMessage(payload, `Feedback request failed with status ${response.status}`),
    );
  }

  const payload: unknown = await response.json();
  if (!isFeedbackResponse(payload)) {
    throw new Error("Feedback response did not match the expected contract");
  }
  return payload;
}
