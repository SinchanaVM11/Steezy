import { fetchHealth, healthUrl } from "./health";

describe("health API client", () => {
  it("normalizes the backend URL without duplicate slashes", () => {
    expect(healthUrl("http://localhost:8000/")).toBe("http://localhost:8000/health");
  });

  it("accepts the backend health response contract", async () => {
    const fetcher = jest.fn(async () =>
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(fetchHealth(fetcher, "http://localhost:8000")).resolves.toEqual({
      status: "ok",
    });
    expect(fetcher).toHaveBeenCalledWith("http://localhost:8000/health");
  });

  it("rejects non-success responses", async () => {
    const fetcher = jest.fn(async () => new Response(null, { status: 503 }));

    await expect(fetchHealth(fetcher)).rejects.toThrow("status 503");
  });
});
