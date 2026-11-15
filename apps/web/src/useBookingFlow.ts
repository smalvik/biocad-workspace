import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type {
  Booking,
  BookingPayload,
  Floor,
  Session,
  Space,
  TimeWindow,
} from "./types";

export type BookingIntent = {
  key: string;
  payload: BookingPayload;
  kind: Space["kind"];
  office: string;
  floor: string;
  attempted: boolean;
  proposalToken?: string;
};

function restored(storageKey: string): BookingIntent | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(storageKey) ?? "null");
    if (
      value &&
      /^(?:[0-9a-f]{32}|[0-9a-f-]{36})$/.test(value.key) &&
      value.attempted === true &&
      (value.proposalToken === undefined ||
        (typeof value.proposalToken === "string" &&
          value.proposalToken.length <= 2048)) &&
      typeof value.payload?.space_id === "string" &&
      value.payload.space_id.length <= 64 &&
      Number.isFinite(Date.parse(value.payload.start_at)) &&
      Number.isFinite(Date.parse(value.payload.end_at)) &&
      Date.parse(value.payload.start_at) < Date.parse(value.payload.end_at) &&
      ["DESK", "MEETING_ROOM"].includes(value.kind) &&
      typeof value.office === "string" &&
      typeof value.floor === "string"
    )
      return value as BookingIntent;
  } catch {
    /* Storage may be disabled; in-memory retries still retain the key. */
  }
  return null;
}

export function useBookingFlow(
  session: Session,
  onExpired: () => void,
  onMutated: () => void,
) {
  const storageKey = `biocad.booking-intent.v1.${session.employee.id}`;
  const [intent, setIntent] = useState<BookingIntent | null>(() =>
    restored(storageKey),
  );
  const [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [result, setResult] = useState<Booking | null>(null);
  const [uncertain, setUncertain] = useState(() => Boolean(intent));
  const locked = useRef(false),
    mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const save = (value: BookingIntent | null) => {
    try {
      if (value) sessionStorage.setItem(storageKey, JSON.stringify(value));
      else sessionStorage.removeItem(storageKey);
    } catch {
      /* Private browsing/quota failures must not prevent booking. */
    }
  };
  const begin = (
    space: Pick<
      Space,
      "id" | "kind" | "desk_mode" | "is_available_for_full_interval"
    >,
    floor: Pick<Floor, "office_name" | "name">,
    window: TimeWindow,
    proposalToken?: string,
  ) => {
    if (locked.current) return;
    if (intent?.attempted && uncertain) {
      setError(
        "Сначала проверьте исходное подтверждение. Место и время сохранены без изменений.",
      );
      setOpen(true);
      return;
    }
    if (
      space.desk_mode === "DEDICATED" ||
      !space.is_available_for_full_interval
    )
      return;
    setIntent({
      // getRandomValues is available on the isolated HTTP test origin as well as
      // HTTPS/localhost; randomUUID requires a secure context. 128 random bits.
      key: Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) =>
        byte.toString(16).padStart(2, "0"),
      ).join(""),
      payload: { space_id: space.id, start_at: window.from, end_at: window.to },
      kind: space.kind,
      office: floor.office_name,
      floor: floor.name,
      attempted: false,
      ...(proposalToken ? { proposalToken } : {}),
    });
    setResult(null);
    setError("");
    setNotice("");
    setUncertain(false);
    setOpen(true);
  };
  const confirm = async () => {
    if (!intent || locked.current || result) return;
    locked.current = true;
    setBusy(true);
    setError("");
    const frozen = { ...intent, attempted: true };
    setIntent(frozen);
    save(frozen);
    try {
      const booking = await (frozen.proposalToken
        ? api.confirmProposal(
            frozen.proposalToken,
            frozen.key,
            session.csrf_token,
          )
        : api.createBooking(frozen.payload, frozen.key, session.csrf_token));
      if (
        booking.space_id !== frozen.payload.space_id ||
        Date.parse(booking.start_at) !== Date.parse(frozen.payload.start_at) ||
        Date.parse(booking.end_at) !== Date.parse(frozen.payload.end_at) ||
        booking.employee_id !== session.employee.id
      )
        throw new ApiError(
          "Сервис вернул другой ресурс или период. Повторите проверку подтверждения.",
        );
      save(null);
      if (!mounted.current) return;
      setResult(booking);
      setUncertain(false);
      setNotice(
        booking.status === "cancelled"
          ? "Исходная бронь уже отменена. Новая бронь не создавалась."
          : "Бронь подтверждена",
      );
      onMutated();
    } catch (reason) {
      if (!mounted.current) return;
      const status = reason instanceof ApiError ? reason.status : 0;
      const unknown = !status || status >= 500 || status === 408;
      setUncertain(unknown);
      if (!unknown && status !== 401) save(null);
      setError(
        reason instanceof Error
          ? reason.message
          : "Не удалось подтвердить бронь",
      );
      if (status === 409) onMutated();
      if (status === 401) onExpired();
    } finally {
      locked.current = false;
      if (mounted.current) setBusy(false);
    }
  };
  const close = () => {
    if (locked.current) return;
    setOpen(false);
    if (!uncertain) {
      setIntent(null);
      setResult(null);
      save(null);
    }
  };
  const resume = useCallback(() => setOpen(true), []);
  return {
    intent,
    open,
    busy,
    error,
    result,
    uncertain,
    notice,
    begin,
    confirm,
    close,
    resume,
  };
}
