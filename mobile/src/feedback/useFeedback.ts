import { useCallback, useRef, useState } from "react";

import { FeedbackAction, FeedbackResponse, submitFeedback } from "../api/feedback";

export type FeedbackSubmissionState =
  | { status: "idle"; response: FeedbackResponse | null }
  | { status: "submitting"; response: FeedbackResponse | null }
  | { status: "success"; response: FeedbackResponse }
  | { status: "error"; response: FeedbackResponse | null; message: string };

export function feedbackStateReducer(
  state: FeedbackSubmissionState,
  action:
    | { type: "submit" }
    | { type: "success"; response: FeedbackResponse }
    | { type: "error"; message: string },
): FeedbackSubmissionState {
  switch (action.type) {
    case "submit":
      return { status: "submitting", response: state.response };
    case "success":
      return { status: "success", response: action.response };
    case "error":
      return { status: "error", response: state.response, message: action.message };
  }
}

export function useFeedback(userId: string, baseUrl: string) {
  const [states, setStates] = useState<Record<string, FeedbackSubmissionState>>({});
  const inFlight = useRef(new Set<string>());

  const submit = useCallback(
    async (wardrobeItemId: string, action: FeedbackAction) => {
      if (!userId.trim() || inFlight.current.has(wardrobeItemId)) {
        return;
      }

      inFlight.current.add(wardrobeItemId);
      setStates((current) => ({
        ...current,
        [wardrobeItemId]: feedbackStateReducer(
          current[wardrobeItemId] ?? { status: "idle", response: null },
          { type: "submit" },
        ),
      }));
      try {
        const response = await submitFeedback(
          fetch,
          baseUrl,
          userId,
          wardrobeItemId,
          action,
        );
        setStates((current) => ({
          ...current,
          [wardrobeItemId]: { status: "success", response },
        }));
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to submit feedback.";
        setStates((current) => ({
          ...current,
          [wardrobeItemId]: feedbackStateReducer(
            current[wardrobeItemId] ?? { status: "idle", response: null },
            { type: "error", message },
          ),
        }));
      } finally {
        inFlight.current.delete(wardrobeItemId);
      }
    },
    [baseUrl, userId],
  );

  return {
    states,
    submit,
    stateFor: (itemId: string): FeedbackSubmissionState =>
      states[itemId] ?? { status: "idle", response: null },
  };
}
