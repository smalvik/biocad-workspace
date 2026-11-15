import type {
  Booking,
  BookingPayload,
  OwnBooking,
  EmployeeLocationResponse,
  EmployeeSearchResponse,
  Floor,
  Session,
  Snapshot,
  TimeWindow,
  ChatResponse,
  ChatMessage,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status = 0,
    readonly code = "",
  ) {
    super(message);
  }
}

async function request<T>(
  url: string,
  options: RequestInit = {},
  timeout = 12_000,
): Promise<T> {
  const controller = new AbortController();
  const external = options.signal;
  const abort = () => controller.abort();
  if (external?.aborted) controller.abort();
  external?.addEventListener("abort", abort, { once: true });
  let timedOut = false;
  const deadline = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
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
        body?.error?.code ?? "",
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
  chat: (
    message: string,
    history: ChatMessage[],
    context: {
      floor_id: string;
      start_at: string;
      end_at: string;
      floors: { id: string; name: string; number: number }[];
    },
    csrf: string,
    signal: AbortSignal,
  ) =>
    request<ChatResponse>(
      "/api/v1/assistant/chat",
      {
        method: "POST",
        body: JSON.stringify({ message, history, context, consent: true }),
        headers: { "X-CSRF-Token": csrf },
        signal,
      },
      70_000,
    ),
  confirmProposal: (
    proposal_token: string,
    idempotency_key: string,
    csrf: string,
  ) =>
    request<Booking>(
      "/api/v1/assistant/confirm",
      {
        method: "POST",
        body: JSON.stringify({ proposal_token, idempotency_key }),
        headers: { "X-CSRF-Token": csrf },
      },
      20_000,
    ),
  createBooking: (payload: BookingPayload, key: string, csrf: string) =>
    request<Booking>("/api/v1/bookings", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": key },
    }),
  myBookings: (signal?: AbortSignal) =>
    request<{ items: OwnBooking[] }>("/api/v1/bookings/me", { signal }),
  cancelBooking: (id: string, csrf: string) =>
    request<Booking>(`/api/v1/bookings/${encodeURIComponent(id)}/cancel`, {
      method: "POST",
      headers: { "X-CSRF-Token": csrf },
    }),
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
  employees: (q: string, window: TimeWindow, signal?: AbortSignal) => {
    const params = new URLSearchParams({ q, from: window.from, to: window.to });
    return request<EmployeeSearchResponse>(`/api/v1/employees?${params}`, {
      signal,
    });
  },
  employeeLocation: async (
    id: string,
    window: TimeWindow,
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams({ from: window.from, to: window.to });
    const result = await request<EmployeeLocationResponse>(
      `/api/v1/employees/${encodeURIComponent(id)}/location?${params}`,
      { signal },
    );
    if (result.employee?.id !== id)
      throw new ApiError(
        "Получены данные другого сотрудника. Повторите поиск.",
      );
    return result;
  },
};
