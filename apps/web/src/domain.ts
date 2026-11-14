import type { Filters, Space, SpaceStatus, TimeWindow } from "./types";

export const DEFAULT_FILTERS: Filters = {
  freedesk: true,
  dedicated: true,
  meeting: true,
  availableOnly: false,
};
export const STATUS_LABELS: Record<SpaceStatus, string> = {
  free: "Свободно",
  booked: "Забронировано",
  dedicated: "Постоянное место",
  mine: "Моя бронь",
};

export function statusOf(space: Space): SpaceStatus {
  if (space.desk_mode === "DEDICATED") return "dedicated";
  if (space.is_available_for_full_interval) return "free";
  return space.reservations.length > 0 &&
    space.reservations.every((row) => row.is_mine)
    ? "mine"
    : "booked";
}

export function matches(space: Space, filters: Filters): boolean {
  if (filters.availableOnly && !space.is_available_for_full_interval)
    return false;
  if (space.kind === "MEETING_ROOM") return filters.meeting;
  return space.desk_mode === "DEDICATED" ? filters.dedicated : filters.freedesk;
}

export function timeWindow(
  date: string,
  start: string,
  end: string,
): TimeWindow | null {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    !/^\d{2}:\d{2}$/.test(start) ||
    !/^\d{2}:\d{2}$/.test(end)
  )
    return null;
  const from = `${date}T${start}:00+03:00`,
    to = `${date}T${end}:00+03:00`;
  if (
    !Number.isFinite(Date.parse(from)) ||
    !Number.isFinite(Date.parse(to)) ||
    Date.parse(from) >= Date.parse(to)
  )
    return null;
  if (
    new Date(Date.parse(from) + 3 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10) !== date
  )
    return null;
  return { from, to };
}

export function moscowTime(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone: "Europe/Moscow",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function moscowDate(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone: "Europe/Moscow",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso));
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function resourceLabel(space: Space): string {
  return `${space.id}, ${space.kind === "MEETING_ROOM" ? "переговорная" : "рабочее место"}, ${STATUS_LABELS[statusOf(space)]}${space.reservations.length > 1 ? `, ${space.reservations.length} брони` : ""}`;
}
