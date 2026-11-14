import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";
import { useSnapshot } from "./useSnapshot";
import type { Snapshot, TimeWindow } from "./types";

const first = {
  from: "2026-11-16T10:00:00+03:00",
  to: "2026-11-16T12:00:00+03:00",
};
const second = {
  from: "2026-11-16T12:00:00+03:00",
  to: "2026-11-16T14:00:00+03:00",
};
const snapshot = (window: TimeWindow): Snapshot => ({
  ...window,
  floor_id: "floor-2",
  snapshot_at: "2026-11-14T10:00:00Z",
  items: [],
});
afterEach(() => vi.restoreAllMocks());

describe("calendar request consistency", () => {
  it("rejects an old response even when the transport resolves after abort", async () => {
    const pending: ((value: Snapshot) => void)[] = [];
    vi.spyOn(api, "snapshot").mockImplementation(
      () => new Promise((resolve) => pending.push(resolve)),
    );
    const expired = vi.fn();
    const { result, rerender } = renderHook(
      ({ window }) => useSnapshot("floor-2", window, expired),
      { initialProps: { window: first } },
    );
    rerender({ window: second });
    await act(async () => pending[1](snapshot(second)));
    expect(result.current.snapshot?.from).toBe(second.from);
    await act(async () => pending[0](snapshot(first)));
    expect(result.current.snapshot?.from).toBe(second.from);
    expect(expired).not.toHaveBeenCalled();
  });
  it("clears the old snapshot while a new date or time is loading", async () => {
    vi.spyOn(api, "snapshot")
      .mockResolvedValueOnce(snapshot(first))
      .mockImplementationOnce(() => new Promise(() => {}));
    const expired = vi.fn();
    const { result, rerender } = renderHook(
      ({ window }) => useSnapshot("floor-2", window, expired),
      { initialProps: { window: first } },
    );
    await waitFor(() => expect(result.current.status).toBe("ready"));
    rerender({ window: second });
    expect(result.current.snapshot).toBeNull();
    expect(result.current.status).toBe("loading");
  });
});
