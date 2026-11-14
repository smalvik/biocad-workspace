import type { Floor, Session, Snapshot, TimeWindow } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status = 0,
  ) {
    super(message);
  }
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const external = options.signal;
  const abort = () => controller.abort();
  if (external?.aborted) controller.abort();
  external?.addEventListener("abort", abort, { once: true });
  let timedOut = false;
  const deadline = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, 12_000);
  try {
    const response = await fetch(url, {
      ...options,
      credentials: "same-origin",
      signal: controller.signal,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
    if (response.status === 204) return undefined as T;
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(
        body?.error?.message ??
          "Не удалось загрузить данные. Повторите попытку.",
        response.status,
      );
    }
    if (body === null)
      throw new ApiError(
        "Не удалось прочитать ответ сервиса. Повторите попытку.",
      );
    return body as T;
  } catch (error) {
    if (timedOut)
      throw new ApiError("Сервис не ответил вовремя. Повторите попытку.");
    if (external?.aborted || error instanceof ApiError) throw error;
    throw new ApiError("Нет соединения с сервисом. Повторите попытку.");
  } finally {
    clearTimeout(deadline);
    external?.removeEventListener("abort", abort);
  }
}

export const api = {
  me: (signal?: AbortSignal) => request<Session>("/api/v1/auth/me", { signal }),
  login: (username: string, password: string) =>
    request<Session>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: (csrf: string) =>
    request<void>("/api/v1/auth/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrf },
    }),
  floors: (signal?: AbortSignal) =>
    request<{ items: Floor[] }>("/api/v1/floors", { signal }),
  snapshot: (floor: string, window: TimeWindow, signal?: AbortSignal) => {
    const params = new URLSearchParams({
      floor_id: floor,
      from: window.from,
      to: window.to,
    });
    return request<Snapshot>(`/api/v1/spaces?${params}`, { signal });
  },
};
