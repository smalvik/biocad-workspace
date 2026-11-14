import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { PeriodResponse, TimeWindow } from "./types";

function usePeriodData<T extends PeriodResponse>(
  value: string,
  window: TimeWindow | null,
  loader: (
    value: string,
    window: TimeWindow,
    signal?: AbortSignal,
  ) => Promise<T>,
  onExpired: () => void,
  delay = 0,
  externalRevision = 0,
) {
  type State = {
    key: string;
    data: T | null;
    status: "idle" | "loading" | "ready" | "error";
    error: string;
  };
  const [state, setState] = useState<State>({
    key: "",
    data: null,
    status: "idle",
    error: "",
  });
  const [revision, setRevision] = useState(0);
  const sequence = useRef(0);
  const refresh = useCallback(() => setRevision((current) => current + 1), []);
  const from = window?.from,
    to = window?.to;
  const key =
    from && to
      ? JSON.stringify([
          value,
          Date.parse(from),
          Date.parse(to),
          revision,
          externalRevision,
        ])
      : "";
  useEffect(() => {
    const id = ++sequence.current;
    const controller = new AbortController();
    setState({ key, data: null, status: key ? "loading" : "idle", error: "" });
    if (!from || !to) return;
    const timer = setTimeout(() => {
      loader(value, { from, to }, controller.signal)
        .then((data) => {
          if (controller.signal.aborted || id !== sequence.current) return;
          if (
            Date.parse(data.from ?? "") !== Date.parse(from) ||
            Date.parse(data.to ?? "") !== Date.parse(to)
          ) {
            throw new ApiError(
              "Получены данные для другого периода. Повторите поиск.",
            );
          }
          setState({ key, data, status: "ready", error: "" });
        })
        .catch((reason) => {
          if (controller.signal.aborted || id !== sequence.current) return;
          if (reason instanceof ApiError && reason.status === 401) {
            onExpired();
            return;
          }
          setState({
            key,
            data: null,
            status: "error",
            error:
              reason instanceof Error
                ? reason.message
                : "Не удалось найти сотрудника",
          });
        });
    }, delay);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value, from, to, loader, onExpired, delay, key]);
  useEffect(() => {
    if (!from || !to) return;
    const timer = setInterval(refresh, 25_000);
    return () => clearInterval(timer);
  }, [from, to, value, refresh]);
  return {
    ...(state.key === key
      ? state
      : {
          data: null,
          status: key ? ("loading" as const) : ("idle" as const),
          error: "",
        }),
    refresh,
  };
}

export function useEmployeeSearch(
  q: string,
  window: TimeWindow | null,
  onExpired: () => void,
  revision = 0,
) {
  return usePeriodData(
    q.trim(),
    window,
    api.employees,
    onExpired,
    250,
    revision,
  );
}

export function useEmployeeLocation(
  id: string | null,
  window: TimeWindow | null,
  onExpired: () => void,
) {
  return usePeriodData(
    id ?? "",
    id ? window : null,
    api.employeeLocation,
    onExpired,
  );
}
