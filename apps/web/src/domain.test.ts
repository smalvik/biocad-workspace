import { describe, expect, it } from "vitest";
import {
  DEFAULT_FILTERS,
  matches,
  moscowTime,
  statusOf,
  timeWindow,
} from "./domain";
import type { Space } from "./types";

const space: Space = {
  id: "D-03",
  floor_id: "floor-2",
  kind: "DESK",
  desk_mode: "FREEDESK",
  capacity: 1,
  zone: "open-space",
  layout: { x: 50, y: 50, width: 60, height: 40 },
  is_available_for_full_interval: true,
  is_partial: false,
  reservations: [],
  assignments: [],
};

describe("map calendar and states", () => {
  it("uses an explicit Moscow offset and formats stored UTC as Moscow time", () => {
    expect(timeWindow("2026-11-16", "10:00", "12:00")).toEqual({
      from: "2026-11-16T10:00:00+03:00",
      to: "2026-11-16T12:00:00+03:00",
    });
    expect(moscowTime("2026-11-16T07:00:00Z")).toBe("10:00");
    expect(timeWindow("2026-11-16", "12:00", "12:00")).toBeNull();
    expect(timeWindow("2026-11-16", "14:00", "12:00")).toBeNull();
    expect(timeWindow("", "10:00", "12:00")).toBeNull();
    expect(timeWindow("2026-02-30", "10:00", "12:00")).toBeNull();
  });
  it("dedicated desks remain non-free regardless of the selected booking window", () => {
    expect(
      statusOf({
        ...space,
        desk_mode: "DEDICATED",
        is_available_for_full_interval: false,
      }),
    ).toBe("dedicated");
    expect(
      matches(
        {
          ...space,
          desk_mode: "DEDICATED",
          is_available_for_full_interval: false,
        },
        { ...DEFAULT_FILTERS, availableOnly: true },
      ),
    ).toBe(false);
  });
  it("does not call a shared multi-booking interval entirely mine", () => {
    const reservation = {
      booking_id: "a",
      employee_id: "e01",
      start_at: "2026-11-16T07:00:00Z",
      end_at: "2026-11-16T09:00:00Z",
      is_mine: true,
    };
    expect(
      statusOf({
        ...space,
        is_available_for_full_interval: false,
        reservations: [reservation],
      }),
    ).toBe("mine");
    expect(
      statusOf({
        ...space,
        is_available_for_full_interval: false,
        reservations: [
          reservation,
          {
            ...reservation,
            booking_id: "b",
            employee_id: "e02",
            is_mine: false,
          },
        ],
      }),
    ).toBe("booked");
  });
  it("filters independently by type and actual full-interval availability", () => {
    expect(matches(space, { ...DEFAULT_FILTERS, freedesk: false })).toBe(false);
    expect(
      matches(
        { ...space, kind: "MEETING_ROOM", desk_mode: null },
        { ...DEFAULT_FILTERS, freedesk: false },
      ),
    ).toBe(true);
    expect(
      matches(
        { ...space, is_available_for_full_interval: false, is_partial: true },
        { ...DEFAULT_FILTERS, availableOnly: true },
      ),
    ).toBe(false);
  });
});
