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
export type PersonPublic = {
  id: string;
  full_name: string;
  job_title: string;
  department: string;
  avatar_url?: string | null;
  fictional: boolean;
};
export type EmployeeLocation = {
  relation: "assignment" | "reservation";
  space_id: string;
  space_kind: "DESK" | "MEETING_ROOM";
  desk_mode: "DEDICATED" | "FREEDESK" | null;
  floor_id: string;
  floor_number: number;
  floor_name: string;
  office_id: string;
  office_name: string;
  booking_id?: string;
  start_at?: string;
  end_at?: string;
  valid_from?: string;
  valid_to?: string | null;
};
export type EmployeeSearchItem = PersonPublic & {
  locations: EmployeeLocation[] | null;
};
export type PeriodResponse = {
  from: string | null;
  to: string | null;
  snapshot_at: string;
};
export type EmployeeSearchResponse = PeriodResponse & {
  items: EmployeeSearchItem[];
};
export type EmployeeLocationResponse = PeriodResponse & {
  employee: PersonPublic;
  locations: EmployeeLocation[];
};
export type Reservation = {
  booking_id: string;
  employee_id: string;
  start_at: string;
  end_at: string;
  is_mine: boolean;
  person_public?: PersonPublic | null;
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
  next_reservation?: { start_at: string; end_at: string } | null;
  reservations: Reservation[];
  assignments: {
    employee_id: string;
    valid_from: string;
    valid_to: string | null;
    person_public?: PersonPublic | null;
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
  employee: PersonPublic;
  csrf_token: string;
};
export type TimeWindow = { from: string; to: string };
export type BookingPayload = {
  space_id: string;
  start_at: string;
  end_at: string;
};
export type Booking = BookingPayload & {
  id: string;
  employee_id: string;
  status: "confirmed" | "cancelled";
  created_at: string;
  cancelled_at: string | null;
};
export type OwnBooking = Booking & {
  resource: {
    kind: "DESK" | "MEETING_ROOM";
    floor_id: string;
    floor_name: string;
    office_name: string;
  };
};
export type SpaceStatus = "free" | "booked" | "dedicated" | "mine";
export type Filters = {
  freedesk: boolean;
  dedicated: boolean;
  meeting: boolean;
  availableOnly: boolean;
};
