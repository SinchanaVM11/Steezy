import { useEffect, useState } from "react";
import { Text } from "react-native";

export type HealthResponse = {
  status: string;
};

export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function healthUrl(baseUrl: string = DEFAULT_API_BASE_URL): string {
  return `${baseUrl.replace(/\/+$/, "")}/health`;
}

export async function fetchHealth(
  fetcher: typeof fetch = fetch,
  baseUrl: string = DEFAULT_API_BASE_URL,
): Promise<HealthResponse> {
  const response = await fetcher(healthUrl(baseUrl));

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();

  if (
    typeof payload !== "object" ||
    payload === null ||
    !("status" in payload) ||
    typeof payload.status !== "string"
  ) {
    throw new Error("Health response did not match the expected contract");
  }

  return { status: payload.status };
}

export function HealthStatus() {
  const [status, setStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    fetchHealth()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <Text>
      Backend: {status === "checking" ? "checking" : status === "ok" ? "connected" : "unavailable"}
    </Text>
  );
}
