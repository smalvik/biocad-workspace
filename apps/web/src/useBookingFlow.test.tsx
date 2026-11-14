import { act, renderHook } from "@testing-library/react";
import { api, ApiError } from "./api";
import { useBookingFlow } from "./useBookingFlow";
import type { Booking, Floor, Session, Space } from "./types";

const session = {
  employee: { id: "e01", full_name: "Вымышленный пользователь" },
  csrf_token: "fictional-csrf",
} as Session;
const space = {
  id: "D-14",
  kind: "DESK",
  desk_mode: "FREEDESK",
  is_available_for_full_interval: true,
} as Space;
const floor = { name: "Этаж 2", office_name: "Москва, Корпус А" } as Floor;
const period = {
  from: "2030-11-16T10:00:00+03:00",
  to: "2030-11-16T12:00:00+03:00",
};
const booked: Booking = {
  id: "booking-1",
  employee_id: "e01",
  space_id: "D-14",
  start_at: "2030-11-16T07:00:00Z",
  end_at: "2030-11-16T09:00:00Z",
  status: "confirmed",
  created_at: "2026-11-15T00:00:00Z",
  cancelled_at: null,
};

beforeEach(() => sessionStorage.clear());
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("supports the isolated HTTP origin where randomUUID is unavailable", () => {
  const getRandomValues = crypto.getRandomValues.bind(crypto);
  vi.stubGlobal("crypto", { getRandomValues });
  const { result } = renderHook(() =>
    useBookingFlow(session, vi.fn(), vi.fn()),
  );
  act(() => result.current.begin(space, floor, period));
  expect(result.current.open).toBe(true);
  expect(result.current.intent?.key).toMatch(/^[0-9a-f]{32}$/);
});

it("does not write before confirmation and freezes the exact resource/period", async () => {
  const create = vi.spyOn(api, "createBooking").mockResolvedValue(booked),
    mutated = vi.fn();
  const { result } = renderHook(() =>
    useBookingFlow(session, vi.fn(), mutated),
  );
  const input = { ...period };
  act(() => result.current.begin(space, floor, input));
  input.from = "2031-01-01T10:00:00+03:00";
  expect(create).not.toHaveBeenCalled();
  await act(() => result.current.confirm());
  expect(create.mock.calls[0][0]).toEqual({
    space_id: "D-14",
    start_at: period.from,
    end_at: period.to,
  });
  expect(create.mock.calls[0][2]).toBe(session.csrf_token);
  expect(result.current.result?.id).toBe(booked.id);
  expect(mutated).toHaveBeenCalledOnce();
});

it("retains the key/payload after lost response and refuses silent retargeting", async () => {
  const create = vi
    .spyOn(api, "createBooking")
    .mockRejectedValueOnce(new ApiError("Соединение потеряно"))
    .mockResolvedValue(booked);
  const { result } = renderHook(() =>
    useBookingFlow(session, vi.fn(), vi.fn()),
  );
  act(() => result.current.begin(space, floor, period));
  await act(() => result.current.confirm());
  act(() => {
    result.current.close();
    result.current.begin({ ...space, id: "D-02" }, floor, period);
  });
  expect(result.current.intent?.payload.space_id).toBe("D-14");
  expect(result.current.uncertain).toBe(true);
  await act(() => result.current.confirm());
  expect(create.mock.calls[1]).toEqual(create.mock.calls[0]);
  expect(result.current.result?.id).toBe(booked.id);
});

it("recovers an in-flight key across remount and reports a cancelled replay honestly", async () => {
  const create = vi
    .spyOn(api, "createBooking")
    .mockRejectedValueOnce(new ApiError("Неизвестный результат", 503))
    .mockResolvedValue({ ...booked, status: "cancelled" });
  const first = renderHook(() => useBookingFlow(session, vi.fn(), vi.fn()));
  act(() => first.result.current.begin(space, floor, period));
  await act(() => first.result.current.confirm());
  first.unmount();
  const second = renderHook(() => useBookingFlow(session, vi.fn(), vi.fn()));
  expect(second.result.current.intent?.key).toBe(create.mock.calls[0][1]);
  await act(() => second.result.current.confirm());
  expect(create.mock.calls[1]).toEqual(create.mock.calls[0]);
  expect(second.result.current.notice).toContain("уже отменена");
  expect(sessionStorage.length).toBe(0);
});

it("guards simultaneous confirms even before a React rerender", async () => {
  let resolve!: (value: Booking) => void;
  const create = vi.spyOn(api, "createBooking").mockImplementation(
    () =>
      new Promise((value) => {
        resolve = value;
      }),
  );
  const { result } = renderHook(() =>
    useBookingFlow(session, vi.fn(), vi.fn()),
  );
  act(() => result.current.begin(space, floor, period));
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.confirm();
    void result.current.confirm();
    result.current.close();
  });
  expect(create).toHaveBeenCalledOnce();
  expect(result.current.open).toBe(true);
  await act(async () => {
    resolve(booked);
    await pending;
  });
});

it("refreshes conflict occupancy and permits an explicitly new choice after a definite rejection", async () => {
  vi.spyOn(api, "createBooking").mockRejectedValue(
    new ApiError("Ресурс уже занят", 409, "BOOKING_CONFLICT"),
  );
  const refresh = vi.fn();
  const { result } = renderHook(() =>
    useBookingFlow(session, vi.fn(), refresh),
  );
  act(() => result.current.begin(space, floor, period));
  const oldKey = result.current.intent?.key;
  await act(() => result.current.confirm());
  expect(result.current.uncertain).toBe(false);
  expect(refresh).toHaveBeenCalledOnce();
  act(() => result.current.close());
  act(() => result.current.begin({ ...space, id: "D-02" }, floor, period));
  expect(result.current.intent?.key).not.toBe(oldKey);
});

it("expires the session on 401 while retaining the original retry identity", async () => {
  vi.spyOn(api, "createBooking").mockRejectedValue(
    new ApiError("Сессия завершена", 401),
  );
  const expired = vi.fn();
  const { result } = renderHook(() =>
    useBookingFlow(session, expired, vi.fn()),
  );
  act(() => result.current.begin(space, floor, period));
  await act(() => result.current.confirm());
  expect(expired).toHaveBeenCalledOnce();
  expect(sessionStorage.length).toBe(1);
});

it("never presents a mismatched success response as this booking", async () => {
  vi.spyOn(api, "createBooking").mockResolvedValue({
    ...booked,
    space_id: "M-01",
  });
  const { result } = renderHook(() =>
    useBookingFlow(session, vi.fn(), vi.fn()),
  );
  act(() => result.current.begin(space, floor, period));
  await act(() => result.current.confirm());
  expect(result.current.result).toBeNull();
  expect(result.current.uncertain).toBe(true);
  expect(result.current.error).toContain("другой ресурс");
});
