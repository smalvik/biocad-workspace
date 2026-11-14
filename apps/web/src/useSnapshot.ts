import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { Snapshot, TimeWindow } from "./types";

export function useSnapshot(
  floorId: string,
  window: TimeWindow | null,
  onExpired: () => void,
) {
  type State = {
    key: string;
    snapshot: Snapshot | null;
    status: "idle" | "loading" | "ready" | "error";
    error: string;
  };
  const [state, setState] = useState<State>({
    key: "",
    snapshot: null,
    status: "idle",
    error: "",
  });
  const [revision, setRevision] = useState(0);
  const sequence = useRef(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  const from = window?.from,
    to = window?.to;
  const key =
    floorId && from && to
      ? `${floorId}/${Date.parse(from)}/${Date.parse(to)}`
      : "";

  useEffect(() => {
    const id = ++sequence.current;
    const controller = new AbortController();
    setState({
      key,
      snapshot: null,
      status: key ? "loading" : "idle",
      error: "",
    });
    if (!floorId || !from || !to) return;
    api
      .snapshot(floorId, { from, to }, controller.signal)
      .then((value) => {
        if (controller.signal.aborted || id !== sequence.current) return;
        if (
          value.floor_id !== floorId ||
          Date.parse(value.from) !== Date.parse(from) ||
          Date.parse(value.to) !== Date.parse(to)
        ) {
          throw new ApiError(
            "Получены данные для другого периода. Обновите доступность.",
          );
        }
        setState({ key, snapshot: value, status: "ready", error: "" });
      })
      .catch((reason) => {
        if (controller.signal.aborted || id !== sequence.current) return;
        if (reason instanceof ApiError && reason.status === 401) {
          onExpired();
          return;
        }
        setState({
          key,
          snapshot: null,
          status: "error",
          error:
            reason instanceof Error
              ? reason.message
              : "Не удалось загрузить план",
        });
      });
    return () => controller.abort();
  }, [floorId, from, to, revision, key, onExpired]);

  useEffect(() => {
    if (!floorId || !from || !to) return;
    const timer = setInterval(refresh, 25_000);
    return () => clearInterval(timer);
  }, [floorId, from, to, refresh]);

  // Hide a prior selection's data during the render before the effect runs.
  return {
    ...(state.key === key
      ? state
      : {
          snapshot: null,
          status: key ? ("loading" as const) : ("idle" as const),
          error: "",
        }),
    refresh,
  };
}
