import { act, renderHook, waitFor } from "@testing-library/react";
import { api, ApiError } from "./api";
import type { EmployeeSearchResponse } from "./types";
import { useEmployeeLocation, useEmployeeSearch } from "./useEmployees";

const period = {
  from: "2026-11-16T10:00:00+03:00",
  to: "2026-11-16T12:00:00+03:00",
};
const response = (id: string): EmployeeSearchResponse => ({
  ...period,
  snapshot_at: "2026-11-14T12:00:00Z",
  items: [
    {
      id,
      full_name: id,
      job_title: "Демо",
      department: "R&D",
      fictional: true,
      locations: [],
    },
  ],
});
afterEach(() => vi.restoreAllMocks());

it("hides prior query data immediately and ignores a late search response even when abort is ignored", async () => {
  let finishOld!: (data: EmployeeSearchResponse) => void;
  const expired = vi.fn();
  vi.spyOn(api, "employees")
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finishOld = resolve;
        }),
    )
    .mockResolvedValueOnce(response("e04"));
  const { result, rerender } = renderHook(
    ({ q }) => useEmployeeSearch(q, period, expired),
    { initialProps: { q: "Мария" } },
  );
  await waitFor(() => expect(api.employees).toHaveBeenCalledTimes(1));
  rerender({ q: "Павел" });
  expect(result.current.data).toBeNull();
  await waitFor(() => expect(result.current.data?.items[0].id).toBe("e04"));
  await act(async () => finishOld(response("e03")));
  expect(result.current.data?.items[0].id).toBe("e04");
});

it("rejects a directory response for a different calendar period", async () => {
  vi.spyOn(api, "employees").mockResolvedValue({
    ...response("e03"),
    from: "2026-11-16T14:00:00+03:00",
  });
  const expired = vi.fn();
  const { result } = renderHook(() =>
    useEmployeeSearch("Мария", period, expired),
  );
  await waitFor(() => expect(result.current.status).toBe("error"));
  expect(result.current.data).toBeNull();
  expect(result.current.error).toMatch(/другого периода/);
  expect(expired).not.toHaveBeenCalled();
});

it("expires the authenticated flow on a location 401", async () => {
  vi.spyOn(api, "employeeLocation").mockRejectedValue(
    new ApiError("Сессия завершена", 401),
  );
  const expired = vi.fn();
  renderHook(() => useEmployeeLocation("e03", period, expired));
  await waitFor(() => expect(expired).toHaveBeenCalledTimes(1));
});
