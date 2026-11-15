import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError } from "./api";
import { moscowDate, moscowTime } from "./domain";
import type { OwnBooking, Session } from "./types";
import type { BookingIntent, useBookingFlow } from "./useBookingFlow";

export function Dialog({
  title,
  busy = false,
  close,
  children,
}: {
  title: string;
  busy?: boolean;
  close: () => void;
  children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = dialog.current!;
    const previous = document.activeElement as HTMLElement | null;
    node.showModal();
    node.querySelector<HTMLElement>("h2")?.focus();
    return () => {
      node.close();
      // React removes the dialog before passive cleanup. Restore explicitly,
      // including when refresh has replaced the original resource action.
      if (previous?.isConnected && previous !== document.body) previous.focus();
      else
        document
          .querySelector<HTMLElement>(".booking-navigation button")
          ?.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      className="booking-dialog"
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
    >
      <div className="booking-dialog-heading">
        <h2 tabIndex={-1}>{title}</h2>
        <button
          className="icon-button"
          aria-label={`Закрыть: ${title}`}
          disabled={busy}
          onClick={close}
        >
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}

function Period({ from, to }: { from: string; to: string }) {
  return (
    <p className="booking-period">
      {moscowDate(from)}
      <br />
      <strong>
        {moscowTime(from)}–{moscowTime(to)} МСК
      </strong>
      {moscowDate(from) !== moscowDate(to) && (
        <>
          <br />
          Окончание: {moscowDate(to)}
        </>
      )}
    </p>
  );
}

function IntentSummary({ intent }: { intent: BookingIntent }) {
  return (
    <div className="booking-summary">
      <strong>
        {intent.kind === "MEETING_ROOM" ? "Переговорная" : "FreeDesk"}{" "}
        {intent.payload.space_id}
      </strong>
      <p>
        {intent.office} · {intent.floor}
      </p>
      <Period from={intent.payload.start_at} to={intent.payload.end_at} />
    </div>
  );
}

function OwnBookings({
  session,
  close,
  onExpired,
  onMutated,
}: {
  session: Session;
  close: () => void;
  onExpired: () => void;
  onMutated: () => void;
}) {
  const [items, setItems] = useState<OwnBooking[] | null>(null),
    [error, setError] = useState("");
  const [revision, setRevision] = useState(0),
    [filter, setFilter] = useState("confirmed");
  const [selected, setSelected] = useState<OwnBooking | null>(null),
    [busy, setBusy] = useState(false);
  const [cancelError, setCancelError] = useState(""),
    [notice, setNotice] = useState("");
  const locked = useRef(false),
    alive = useRef(true);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setItems(null);
    setError("");
    api
      .myBookings(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setItems(value.items);
      })
      .catch((reason) => {
        if (controller.signal.aborted) return;
        if (reason instanceof ApiError && reason.status === 401) onExpired();
        else
          setError(
            reason instanceof Error
              ? reason.message
              : "Не удалось загрузить брони",
          );
      });
    return () => controller.abort();
  }, [revision, onExpired]);
  useEffect(() => {
    const timer = setInterval(refresh, 25_000);
    return () => clearInterval(timer);
  }, [refresh]);
  const cancel = async () => {
    if (!selected || locked.current) return;
    locked.current = true;
    setBusy(true);
    setCancelError("");
    try {
      const result = await api.cancelBooking(selected.id, session.csrf_token);
      if (result.id !== selected.id || result.status !== "cancelled")
        throw new ApiError("Отмена не подтверждена. Повторите проверку.");
      if (!alive.current) return;
      setSelected(null);
      setNotice("Бронь отменена");
      refresh();
      onMutated();
    } catch (reason) {
      if (!alive.current) return;
      setCancelError(
        reason instanceof Error ? reason.message : "Не удалось отменить бронь",
      );
      if (reason instanceof ApiError && reason.status === 401) onExpired();
    } finally {
      locked.current = false;
      if (alive.current) setBusy(false);
    }
  };
  const shown = items?.filter((item) => item.status === filter);
  return (
    <>
      <Dialog title="Мои бронирования" close={close} busy={busy}>
        <p className="muted">Только ваши брони. Дата и время по Москве.</p>
        <div
          className="booking-tabs"
          role="group"
          aria-label="Статус моих броней"
        >
          <button
            className="secondary-button"
            aria-pressed={filter === "confirmed"}
            onClick={() => setFilter("confirmed")}
          >
            Активные
          </button>
          <button
            className="secondary-button"
            aria-pressed={filter === "cancelled"}
            onClick={() => setFilter("cancelled")}
          >
            Отменённые
          </button>
          <button className="text-button" onClick={refresh}>
            Обновить мои брони
          </button>
        </div>
        {notice && (
          <p role="status" className="notice">
            {notice}
          </p>
        )}
        {error ? (
          <div role="alert">
            <p>{error}</p>
            <button className="secondary-button" onClick={refresh}>
              Повторить загрузку броней
            </button>
          </div>
        ) : !items ? (
          <p role="status">Загружаем ваши брони…</p>
        ) : !shown?.length ? (
          <p className="booking-empty">
            {filter === "confirmed"
              ? "У вас пока нет активных броней"
              : "Отменённых броней пока нет"}
          </p>
        ) : (
          <ul className="own-bookings">
            {shown.map((booking) => (
              <li
                key={booking.id}
                className="own-booking"
                data-booking-id={booking.id}
              >
                <strong>
                  {booking.resource.kind === "MEETING_ROOM"
                    ? "Переговорная"
                    : "FreeDesk"}{" "}
                  {booking.space_id}
                </strong>
                <p>
                  {booking.resource.office_name} · {booking.resource.floor_name}
                </p>
                <Period from={booking.start_at} to={booking.end_at} />
                <span className={`booking-state ${booking.status}`}>
                  {booking.status === "cancelled" ? "Отменена" : "Подтверждена"}
                </span>
                <small className="booking-code">Код брони: {booking.id}</small>
                {booking.status === "confirmed" && (
                  <button
                    className="secondary-button danger-button"
                    onClick={() => {
                      setSelected(booking);
                      setCancelError("");
                    }}
                  >
                    Отменить бронь {booking.space_id}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Dialog>
      {selected && (
        <Dialog
          title="Отменить бронирование?"
          busy={busy}
          close={() => {
            if (!locked.current) setSelected(null);
          }}
        >
          <div className="booking-summary">
            <strong>{selected.space_id}</strong>
            <p>
              {selected.resource.office_name} · {selected.resource.floor_name}
            </p>
            <Period from={selected.start_at} to={selected.end_at} />
          </div>
          <p>
            После отмены ресурс станет доступен другим сотрудникам на этот
            интервал.
          </p>
          {cancelError && (
            <p role="alert" className="error-message">
              {cancelError} Повторная отмена безопасна.
            </p>
          )}
          <div className="booking-actions">
            <button
              className="secondary-button"
              disabled={busy}
              onClick={() => setSelected(null)}
            >
              Сохранить бронь
            </button>
            <button
              className="primary-button danger-button"
              disabled={busy}
              onClick={cancel}
            >
              {busy ? "Отменяем…" : "Подтвердить отмену"}
            </button>
          </div>
        </Dialog>
      )}
    </>
  );
}

export function BookingFlow({
  flow,
  session,
  onExpired,
  onMutated,
}: {
  flow: ReturnType<typeof useBookingFlow>;
  session: Session;
  onExpired: () => void;
  onMutated: () => void;
}) {
  const [showOwn, setShowOwn] = useState(false);
  return (
    <>
      <nav className="booking-navigation" aria-label="Бронирования">
        <button className="secondary-button" onClick={() => setShowOwn(true)}>
          Мои бронирования
        </button>
        {flow.intent?.attempted && flow.uncertain && !flow.result && (
          <button className="secondary-button" onClick={flow.resume}>
            Проверить незавершённое подтверждение
          </button>
        )}
        {flow.notice && <span role="status">{flow.notice}</span>}
      </nav>
      {flow.open && flow.intent && (
        <Dialog
          title={
            flow.result
              ? "Результат бронирования"
              : "Подтверждение бронирования"
          }
          busy={flow.busy}
          close={flow.close}
        >
          <IntentSummary intent={flow.intent} />
          <p>
            Бронирует: <strong>{session.employee.full_name}</strong>
          </p>
          {flow.result ? (
            <>
              <p role="status" className="notice">
                {flow.result.status === "cancelled"
                  ? "Исходная бронь уже отменена. Новая бронь не создавалась."
                  : "Бронь подтверждена"}
              </p>
              <p className="booking-code">Код брони: {flow.result.id}</p>
              <div className="booking-actions">
                <button
                  className="secondary-button"
                  onClick={() => {
                    flow.close();
                    setShowOwn(true);
                  }}
                >
                  Посмотреть мои брони
                </button>
                <button className="primary-button" onClick={flow.close}>
                  Готово
                </button>
              </div>
            </>
          ) : (
            <>
              <p className="booking-explanation">
                Проверьте место и точное время. Бронь создаётся только после
                нажатия «Подтвердить бронирование».
              </p>
              {flow.uncertain && (
                <p className="notice">
                  Результат запроса пока неизвестен. Повтор проверит исходную
                  бронь с тем же ключом, без создания копии.
                </p>
              )}
              {flow.error && (
                <p role="alert" className="error-message">
                  {flow.error}
                </p>
              )}
              <div className="booking-actions">
                <button
                  className="secondary-button"
                  disabled={flow.busy}
                  onClick={flow.close}
                >
                  {flow.uncertain ? "Проверить позже" : "Вернуться к выбору"}
                </button>
                <button
                  className="primary-button"
                  disabled={flow.busy}
                  onClick={flow.confirm}
                >
                  {flow.busy
                    ? "Проверяем подтверждение…"
                    : flow.intent.attempted
                      ? "Повторить подтверждение"
                      : "Подтвердить бронирование"}
                </button>
              </div>
            </>
          )}
        </Dialog>
      )}
      {showOwn && (
        <OwnBookings
          session={session}
          close={() => setShowOwn(false)}
          onExpired={onExpired}
          onMutated={onMutated}
        />
      )}
    </>
  );
}
