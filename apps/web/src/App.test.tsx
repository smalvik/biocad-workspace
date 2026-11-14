import { render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App skeleton", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows both services as ok when health endpoints respond", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    render(<App />);
    await waitFor(() => expect(screen.getByTestId("booking-status")).toHaveTextContent("ok"));
    expect(screen.getByTestId("assistant-status")).toHaveTextContent("ok");
  });

  it("marks assistant down without breaking the page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        url.includes("assistant") ? Promise.reject(new Error("down")) : Promise.resolve({ ok: true }),
      ),
    );
    render(<App />);
    await waitFor(() => expect(screen.getByTestId("assistant-status")).toHaveTextContent("down"));
    expect(screen.getByTestId("booking-status")).toHaveTextContent("ok");
  });
});
