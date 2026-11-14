export type Rect = { x: number; y: number; width: number; height: number };
export type Segment = { x1: number; y1: number; x2: number; y2: number };
export type Plan = {
  width: number;
  height: number;
  outline: Rect;
  zones: (Rect & { id: string; kind: string; label: string; note?: string })[];
  walls: Segment[];
  windows: Segment[];
  doors: { x: number; y: number; size: number; vertical?: boolean }[];
  hvac: Rect[];
  plants: { x: number; y: number }[];
};
export type Floor = {
  id: string;
  number: number;
  name: string;
  office_id: string;
  office_name: string;
  plan: Plan;
};
export type Reservation = {
  booking_id: string;
  employee_id: string;
  start_at: string;
  end_at: string;
  is_mine: boolean;
};
export type Space = {
  id: string;
  floor_id: string;
  kind: "DESK" | "MEETING_ROOM";
  desk_mode: "DEDICATED" | "FREEDESK" | null;
  capacity: number;
  zone: string;
  layout: Rect & { label?: string };
  is_available_for_full_interval: boolean;
  is_partial: boolean;
  reservations: Reservation[];
  assignments: {
    employee_id: string;
    valid_from: string;
    valid_to: string | null;
  }[];
};
export type Snapshot = {
  floor_id: string;
  from: string;
  to: string;
  snapshot_at: string;
  items: Space[];
};
export type Session = {
  employee: {
    id: string;
    full_name: string;
    job_title: string;
    department: string;
    fictional: boolean;
  };
  csrf_token: string;
};
export type TimeWindow = { from: string; to: string };
export type SpaceStatus = "free" | "booked" | "dedicated" | "mine";
export type Filters = {
  freedesk: boolean;
  dedicated: boolean;
  meeting: boolean;
  availableOnly: boolean;
};
