import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { api, ApiError } from "./api";
import { Avatar, PersonSummary } from "./Avatar";
import { EmployeeSearch } from "./EmployeeSearch";
import { BookingFlow } from "./BookingFlow";
import { AssistantChat, ProposalSummary } from "./AssistantChat";
import { useBookingFlow } from "./useBookingFlow";
import { useEmployeeLocation } from "./useEmployees";
import {
  DEFAULT_FILTERS,
  matches,
  moscowDate,
  moscowTime,
  STATUS_LABELS,
  statusOf,
  timeWindow,
} from "./domain";
import { FloorMap } from "./FloorMap";
import { Icon } from "./Icon";
import type {
  Filters,
  Floor,
  Session,
  Space,
  SpaceStatus,
  TimeWindow,
  AssistantProposal,
} from "./types";
import { useSnapshot } from "./useSnapshot";

const PRESETS = [
  ["09:00", "17:00"],
  ["10:00", "12:00"],
  ["12:00", "14:00"],
  ["14:00", "16:00"],
];
const FOOTNOTE =
  "Данные и сотрудники вымышлены. Приближённые цвета BIOCAD; официальный UI Kit не предоставлен.";

function Header({
  session,
  logout,
}: {
  session?: Session | null;
  logout?: () => void;
}) {
  return (
    <header className="app-header">
      <a href="/" className="brand" aria-label="BIOCAD Workspace">
        <span>
          BIO<span className="brand-accent">CAD</span>
        </span>
        <span className="brand-divider" />
        <span className="brand-product">Workspace</span>
      </a>
      <div className="header-context">
        <Icon name="map" size={18} /> <span>Карта офиса</span>
      </div>
      {session ? (
        <div className="user-menu">
          <Avatar person={session.employee} />
          <div className="user-name">
            <strong>{session.employee.full_name}</strong>
            <span>Демо-аккаунт</span>
          </div>
          <button className="icon-button" aria-label="Выйти" onClick={logout}>
            <Icon name="logout" />
          </button>
        </div>
      ) : (
        <span className="demo-badge">Демонстрационная среда</span>
      )}
    </header>
  );
}

function StateCard({
  title,
  children,
  action,
  busy = false,
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  busy?: boolean;
}) {
  return (
    <div
      className={`state-card${busy ? " is-loading" : ""}`}
      role={busy ? "status" : "region"}
      aria-label={title}
    >
      <span className="state-icon">
        <Icon name={busy ? "refresh" : "map"} size={34} />
      </span>
      <h2>{title}</h2>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

function Login({
  onLogin,
  notice,
}: {
  onLogin: (session: Session) => void;
  notice: string;
}) {
  const [username, setUsername] = useState("e01"),
    [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await api.login(username, password));
      setPassword("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось войти");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Header />
      <main className="login-layout">
        <section className="login-intro">
          <span className="eyebrow">ВАШ ОФИС. ВАШ РАБОЧИЙ ДЕНЬ.</span>
          <h1>
            Найдите своё
            <br />
            место в офисе<span>.</span>
          </h1>
          <p>
            Рабочие места и переговорные на одном плане.
            <br />
            Актуальная доступность на выбранное время.
          </p>
          <div className="intro-illustration" aria-hidden="true">
            <div className="intro-room" />
            <div className="intro-desk desk-one" />
            <div className="intro-desk desk-two" />
            <div className="intro-desk desk-three" />
            <span className="intro-availability">
              <i /> Все места на одном плане
            </span>
          </div>
          <span className="intro-location">
            <Icon name="pin" size={18} /> Москва · Корпус А
          </span>
        </section>
        <section className="login-card" aria-label="Вход в демо">
          <span className="eyebrow">ДОБРО ПОЖАЛОВАТЬ</span>
          <h2>Войти в Workspace</h2>
          <p className="muted">Используйте демонстрационный аккаунт.</p>
          {notice && (
            <p role="status" className="notice">
              {notice}
            </p>
          )}
          <form onSubmit={submit}>
            <label>
              Логин
              <input
                name="username"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
                maxLength={64}
              />
            </label>
            <label>
              Пароль
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                maxLength={128}
              />
            </label>
            {error && (
              <p role="alert" className="error-message">
                {error}
              </p>
            )}
            <button
              className="primary-button login-submit"
              type="submit"
              disabled={busy}
            >
              {busy ? "Входим…" : "Войти"}
              <Icon name="arrow" size={18} />
            </button>
          </form>
          <div className="demo-credentials">
            <Icon name="info" size={18} />
            <p>
              Демо: <strong>e01–e12</strong>
              <br />
              Пароль по умолчанию: <strong>demo-workspace</strong>
              <br />
              <span>Все аккаунты вымышлены.</span>
            </p>
          </div>
        </section>
      </main>
      <footer className="app-footer">{FOOTNOTE}</footer>
    </>
  );
}

function Legend() {
  return (
    <ul className="map-legend" aria-label="Легенда статусов">
      {(Object.keys(STATUS_LABELS) as SpaceStatus[]).map((status) => (
        <li key={status}>
          <span className={`legend-swatch status-${status}`}>
            {status === "dedicated"
              ? "×"
              : status === "mine"
                ? "✓"
                : status === "booked"
                  ? "—"
                  : ""}
          </span>
          {STATUS_LABELS[status]}
        </li>
      ))}
      <li>
        <span className="legend-selected" />
        Выбрано
      </li>
    </ul>
  );
}

function Details({
  space,
  floor,
  window,
  employeeId,
  onClose,
  lookup,
  lookupActive = false,
  onChooseLocation,
  onShowAvailable,
  onBook,
}: {
  space?: Space;
  floor?: Floor;
  window: TimeWindow | null;
  employeeId: string;
  onClose: () => void;
  lookup?: ReturnType<typeof useEmployeeLocation>;
  lookupActive?: boolean;
  onChooseLocation?: (spaceId: string) => void;
  onShowAvailable?: () => void;
  onBook: (space: Space, floor: Floor, window: TimeWindow) => void;
}) {
  const panel = useRef<HTMLElement>(null);
  const [mobile, setMobile] = useState(
    () =>
      typeof matchMedia !== "undefined" &&
      matchMedia("(max-width: 820px)").matches,
  );
  useEffect(() => {
    if (typeof matchMedia === "undefined") return;
    const query = matchMedia("(max-width: 820px)"),
      change = () => setMobile(query.matches);
    query.addEventListener("change", change);
    return () => query.removeEventListener("change", change);
  }, []);
  const person = lookup?.data?.employee;
  const pendingLookup =
    lookupActive &&
    (lookup?.status !== "ready" ||
      Boolean(lookup.data?.locations.length && !space));
  const modal = mobile && Boolean(space || lookupActive);
  useEffect(() => {
    if (!modal || !panel.current) return;
    const previous = document.activeElement as HTMLElement | null;
    panel.current.querySelector<HTMLElement>("h2")?.focus();
    const keys = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
      if (event.key === "Tab") {
        const buttons = Array.from(
          panel.current?.querySelectorAll<HTMLElement>(
            "button, a[href], input, select",
          ) ?? [],
        );
        const first = buttons[0],
          last = buttons[buttons.length - 1];
        if (
          event.shiftKey &&
          (document.activeElement === first ||
            document.activeElement?.tagName === "H2")
        ) {
          event.preventDefault();
          last?.focus();
        } else if (
          !event.shiftKey &&
          (document.activeElement === last ||
            !panel.current?.contains(document.activeElement))
        ) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", keys);
    return () => {
      document.removeEventListener("keydown", keys);
      previous?.focus();
    };
  }, [modal, space?.id, person?.id, onClose]);
  const status = space ? statusOf(space) : null;
  return (
    <>
      {modal && (
        <div className="sheet-backdrop" onClick={onClose} aria-hidden="true" />
      )}
      <aside
        ref={panel}
        className={`details-panel${space || lookupActive ? " has-selection" : ""}`}
        aria-label={
          lookupActive && !space ? "Детали сотрудника" : "Детали места"
        }
        role={modal ? "dialog" : undefined}
        aria-modal={modal || undefined}
      >
        <div className="panel-eyebrow">ДЕТАЛИ МЕСТА</div>
        {pendingLookup ? (
          <>
            <div className="details-title">
              <h2 tabIndex={-1}>
                {lookup?.status === "error"
                  ? "Не удалось уточнить брони"
                  : "Ищем брони и закрепления"}
              </h2>
              <button
                className="icon-button"
                aria-label="Закрыть карточку сотрудника"
                onClick={onClose}
              >
                <Icon name="close" />
              </button>
            </div>
            {lookup?.status === "error" ? (
              <>
                <p role="alert">{lookup.error}</p>
                <button className="secondary-button" onClick={lookup.refresh}>
                  Повторить поиск сотрудника
                </button>
              </>
            ) : (
              <p role="status">Загружаем сведения на выбранное время…</p>
            )}
          </>
        ) : space && status && floor && window ? (
          <>
            <div className="details-title">
              <h2 tabIndex={-1}>
                {space.kind === "MEETING_ROOM"
                  ? `Переговорная ${space.id}`
                  : `${space.desk_mode === "DEDICATED" ? "Рабочее место" : "FreeDesk"} ${space.id}`}
                {space.desk_mode === "DEDICATED" && (
                  <span className="sr-only">, постоянное место</span>
                )}
              </h2>
              <button
                className="icon-button"
                aria-label="Закрыть карточку места"
                onClick={onClose}
              >
                <Icon name="close" />
              </button>
            </div>
            <div className={`status-badge status-${status}`}>
              {status === "dedicated" && <Icon name="lock" size={15} />}
              {STATUS_LABELS[status]}
            </div>
            {space.layout.label && (
              <p className="room-title">{space.layout.label}</p>
            )}
            <div className="detail-location">
              <Icon name="pin" size={17} />
              <span>
                {floor.office_name}
                <br />
                {floor.name} ·{" "}
                {space.zone === "meeting"
                  ? "Зона переговорных"
                  : "Рабочая зона"}
              </span>
            </div>
            <div className="selected-period">
              <span>ВЫБРАННЫЙ ПЕРИОД</span>
              <strong>{moscowDate(window.from)}</strong>
              <p>
                <Icon name="clock" size={17} />
                {moscowTime(window.from)}–{moscowTime(window.to)}{" "}
                <span>МСК</span>
              </p>
            </div>
            {space.kind === "MEETING_ROOM" && (
              <p className="capacity-line">
                Вместимость <strong>{space.capacity} мест</strong>
              </p>
            )}
            {status === "dedicated" ? (
              <section
                className="assignment-list"
                aria-label="Закрепления на выбранное время"
              >
                {space.assignments.map((assignment) => (
                  <div
                    key={`${assignment.employee_id}-${assignment.valid_from}`}
                    className="assignment-person"
                  >
                    <span className="detail-overline">ЗАКРЕПЛЕНО ЗА</span>
                    {assignment.person_public && (
                      <PersonSummary person={assignment.person_public} />
                    )}
                    <p className="assignment-dates">
                      С {moscowDate(assignment.valid_from)}
                      {assignment.valid_to
                        ? ` до ${moscowDate(assignment.valid_to)} ${moscowTime(assignment.valid_to)} МСК`
                        : " · бессрочно"}
                    </p>
                  </div>
                ))}
                <p className="detail-note">
                  <Icon name="lock" size={18} />
                  <span>
                    {space.assignments.some(
                      (assignment) => assignment.employee_id === employeeId,
                    )
                      ? "Ваше постоянное место."
                      : "Место закреплено постоянно."}{" "}
                    Бронирование недоступно.
                  </span>
                </p>
                {onShowAvailable && (
                  <button
                    className="secondary-button"
                    onClick={onShowAvailable}
                  >
                    Показать свободные FreeDesk
                  </button>
                )}
              </section>
            ) : space.is_available_for_full_interval ? (
              <>
                <p className="free-note">
                  <Icon name="check" size={19} />
                  Доступно на весь выбранный интервал
                </p>
                {Date.parse(window.from) <= Date.now() && (
                  <p role="alert" className="error-message">
                    Выберите начало бронирования в будущем.
                  </p>
                )}
                <button
                  className="primary-button booking-continue"
                  disabled={Date.parse(window.from) <= Date.now()}
                  onClick={() => onBook(space, floor, window)}
                >
                  Продолжить
                </button>
              </>
            ) : (
              <section
                className="reservation-list"
                aria-label="Брони на выбранное время"
              >
                <h3>
                  {space.reservations.length > 1
                    ? `${space.reservations.length} брони в этом интервале`
                    : "Бронь в этом интервале"}
                </h3>
                {space.reservations.map((row) => (
                  <div key={row.booking_id} className="reservation-row">
                    <span className="reservation-point" />
                    <div>
                      {row.person_public && (
                        <PersonSummary person={row.person_public} compact />
                      )}
                      <strong>
                        {moscowTime(row.start_at)}–{moscowTime(row.end_at)} МСК
                      </strong>
                      <span>{moscowDate(row.start_at)}</span>
                      {moscowDate(row.start_at) !== moscowDate(row.end_at) && (
                        <span>
                          Окончание: {moscowDate(row.end_at)}{" "}
                          {moscowTime(row.end_at)} МСК
                        </span>
                      )}
                      <small>
                        {row.is_mine
                          ? "Ваша бронь"
                          : "Забронировано другим сотрудником"}
                      </small>
                    </div>
                  </div>
                ))}
                {space.is_partial && (
                  <p className="muted">
                    Полный выбранный интервал недоступен. Можно выбрать
                    свободное время.
                  </p>
                )}
              </section>
            )}
            {space.is_available_for_full_interval && space.next_reservation && (
              <div className="next-reservation">
                <span>Следующая бронь</span>
                <strong>
                  {moscowDate(space.next_reservation.start_at)} ·{" "}
                  {moscowTime(space.next_reservation.start_at)} МСК
                </strong>
              </div>
            )}
            {lookupActive &&
              lookup?.data &&
              lookup.data.locations.length > 1 && (
                <section
                  className="employee-location-options"
                  aria-label="Брони и закрепления сотрудника"
                >
                  <h3>Брони и закрепления: {person?.full_name}</h3>
                  {lookup.data.locations.map((location, index) => (
                    <button
                      key={`${location.space_id}-${index}`}
                      className="location-option"
                      aria-pressed={space.id === location.space_id}
                      onClick={() => onChooseLocation?.(location.space_id)}
                    >
                      <strong>
                        {location.space_id} · {location.floor_name}
                      </strong>
                      <span>
                        {location.relation === "assignment"
                          ? "Постоянное закрепление"
                          : `${moscowDate(location.start_at!)} · ${moscowTime(location.start_at!)}–${moscowTime(location.end_at!)} МСК`}
                      </span>
                    </button>
                  ))}
                </section>
              )}
            <p className="presence-note">
              Бронь или закрепление не подтверждает физическое присутствие.
            </p>
          </>
        ) : lookupActive &&
          person &&
          window &&
          lookup?.data?.locations.length === 0 ? (
          <>
            <div className="details-title">
              <h2 tabIndex={-1}>{person.full_name}</h2>
              <button
                className="icon-button"
                aria-label="Закрыть карточку сотрудника"
                onClick={onClose}
              >
                <Icon name="close" />
              </button>
            </div>
            <PersonSummary person={person} />
            <div className="selected-period">
              <strong>{moscowDate(window.from)}</strong>
              <p>
                {moscowTime(window.from)}–{moscowTime(window.to)} МСК
              </p>
            </div>
            <p className="employee-empty-location">
              Брони или закрепления на выбранный интервал не найдены.
            </p>
            <p className="presence-note">
              Это не означает, что сотрудника нет в офисе: данные о физическом
              присутствии не собираются.
            </p>
          </>
        ) : (
          <>
            <h2>Выберите место на плане</h2>
            <p className="muted">Посмотрите доступность и детали.</p>
            <div className="details-empty">
              <span>
                <Icon name="map" size={48} />
              </span>
              <h3>Место для вашего дня</h3>
              <p>
                Нажмите на рабочее место или переговорную. Статус зависит от
                даты и времени.
              </p>
            </div>
          </>
        )}
      </aside>
    </>
  );
}

function Workspace({
  session,
  onExpired,
  onLogout,
  notice,
}: {
  session: Session;
  onExpired: () => void;
  onLogout: () => void;
  notice: string;
}) {
  const [floors, setFloors] = useState<Floor[]>([]),
    [floorId, setFloorId] = useState("");
  const [floorError, setFloorError] = useState(""),
    [floorLoading, setFloorLoading] = useState(true),
    [floorRevision, reloadFloors] = useState(0);
  const [date, setDate] = useState("2026-11-16"),
    [start, setStart] = useState("10:00"),
    [end, setEnd] = useState("12:00");
  const [filters, setFilters] = useState<Filters>({ ...DEFAULT_FILTERS }),
    [selectedId, setSelectedId] = useState<string | null>(null);
  const [lookupEmployeeId, setLookupEmployeeId] = useState<string | null>(null);
  const [lookupTarget, setLookupTarget] = useState<string | null>(null);
  const window = useMemo(
    () => timeWindow(date, start, end),
    [date, start, end],
  );
  const closeDetails = useCallback(() => {
    setSelectedId(null);
    setLookupEmployeeId(null);
    setLookupTarget(null);
  }, []);
  const lookup = useEmployeeLocation(lookupEmployeeId, window, onExpired);
  const active = floors.find((floor) => floor.id === floorId);
  const { snapshot, status, error, refresh } = useSnapshot(
    floorId,
    window,
    onExpired,
  );
  const [bookingRevision, setBookingRevision] = useState(0);
  const refreshLookup = lookup.refresh;
  const afterMutation = useCallback(() => {
    refresh();
    refreshLookup();
    setBookingRevision((value) => value + 1);
  }, [refresh, refreshLookup]);
  const bookingFlow = useBookingFlow(session, onExpired, afterMutation);
  const [chatOpen, setChatOpen] = useState(false);
  const [assistantProposal, setAssistantProposal] =
    useState<AssistantProposal | null>(null);
  const applyProposal = (proposal: AssistantProposal) => {
    closeDetails();
    setFilters({ ...DEFAULT_FILTERS });
    setFloorId(proposal.floor.id);
    setDate(
      new Intl.DateTimeFormat("sv-SE", {
        timeZone: "Europe/Moscow",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(new Date(proposal.selection.start_at)),
    );
    setStart(moscowTime(proposal.selection.start_at));
    setEnd(moscowTime(proposal.selection.end_at));
    setSelectedId(proposal.selection.space_id);
    setAssistantProposal(proposal);
    refresh();
  };
  useEffect(() => {
    if (
      assistantProposal &&
      (!window ||
        floorId !== assistantProposal.floor.id ||
        Date.parse(window.from) !==
          Date.parse(assistantProposal.selection.start_at) ||
        Date.parse(window.to) !==
          Date.parse(assistantProposal.selection.end_at))
    )
      setAssistantProposal(null);
  }, [assistantProposal, floorId, window]);
  useEffect(() => {
    if (!lookup.data) return;
    const location =
      lookup.data.locations.find((item) => item.space_id === lookupTarget) ??
      lookup.data.locations[0];
    if (location) {
      setFilters({ ...DEFAULT_FILTERS });
      setFloorId(location.floor_id);
      setSelectedId(location.space_id);
      refresh();
    } else setSelectedId(null);
  }, [lookup.data, lookupTarget, refresh]);
  useEffect(() => {
    const controller = new AbortController();
    setFloorLoading(true);
    setFloorError("");
    api
      .floors(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setFloors(result.items);
        setFloorId((current) =>
          result.items.some((floor) => floor.id === current)
            ? current
            : (result.items[0]?.id ?? ""),
        );
        setFloorLoading(false);
      })
      .catch((reason) => {
        if (controller.signal.aborted) return;
        if (reason instanceof ApiError && reason.status === 401) {
          onExpired();
          return;
        }
        setFloorError(
          reason instanceof Error
            ? reason.message
            : "Не удалось загрузить этажи",
        );
        setFloorLoading(false);
      });
    return () => controller.abort();
  }, [floorRevision, onExpired]);
  const visible =
    snapshot?.items.filter((space) => matches(space, filters)) ?? [];
  const selected =
    lookupEmployeeId && lookup.status !== "ready"
      ? undefined
      : visible.find((space) => space.id === selectedId);
  const selectSpace = (id: string | null) => {
    setAssistantProposal(null);
    setLookupEmployeeId(null);
    setLookupTarget(null);
    setSelectedId(id);
  };
  const freeDesks =
    snapshot?.items.filter(
      (space) => space.kind === "DESK" && space.is_available_for_full_interval,
    ).length ?? 0;
  const offices = Array.from(
    new Map(
      floors.map((floor) => [floor.office_id, floor.office_name]),
    ).entries(),
  );
  const selectFloor = (id: string) => {
    setAssistantProposal(null);
    setFloorId(id);
    closeDetails();
  };
  const filter = (key: keyof Filters, checked: boolean) => {
    setAssistantProposal(null);
    setFilters((current) => ({ ...current, [key]: checked }));
    closeDetails();
  };
  const planReady = active?.plan?.width && active?.plan?.outline;

  return (
    <>
      <Header session={session} logout={onLogout} />
      <main className="workspace">
        {notice && (
          <p className="notice" role="alert">
            {notice}
          </p>
        )}
        <section className="page-intro">
          <div>
            <span className="eyebrow">WORKSPACE BOOKING</span>
            <h1>Карта офиса</h1>
            <p>Выберите этаж и подходящее место на плане.</p>
          </div>
          <span className="moscow-badge">
            <Icon name="pin" size={17} />
            Москва · МСК
          </span>
        </section>
        <BookingFlow
          flow={bookingFlow}
          session={session}
          onExpired={onExpired}
          onMutated={afterMutation}
        />
        <div className="assistant-navigation">
          <button
            className="secondary-button"
            disabled={!active || !window || bookingFlow.busy}
            onClick={() => {
              setAssistantProposal(null);
              setChatOpen(true);
            }}
          >
            AI-ассистент
          </button>
        </div>
        {assistantProposal && (
          <section className="assistant-proposal" aria-label="Предложение AI">
            <ProposalSummary proposal={assistantProposal} />
            <div className="booking-actions">
              <button
                className="secondary-button"
                onClick={() => setAssistantProposal(null)}
              >
                Отклонить предложение
              </button>
              <button
                className="primary-button"
                onClick={() => {
                  const proposal = assistantProposal;
                  setAssistantProposal(null);
                  closeDetails();
                  bookingFlow.begin(
                    proposal.space,
                    proposal.floor,
                    {
                      from: proposal.selection.start_at,
                      to: proposal.selection.end_at,
                    },
                    proposal.token,
                  );
                }}
              >
                Проверить предложение AI
              </button>
            </div>
          </section>
        )}
        {chatOpen && active && window && (
          <AssistantChat
            session={session}
            floor={active}
            floors={floors}
            window={window}
            close={() => setChatOpen(false)}
            onExpired={onExpired}
            onProposal={applyProposal}
          />
        )}
        <div className="workspace-grid">
          <aside className="filter-panel" aria-label="Фильтры карты">
            <EmployeeSearch
              window={window}
              selectedId={lookupEmployeeId}
              onExpired={onExpired}
              revision={bookingRevision}
              onSelect={(id) => {
                setAssistantProposal(null);
                setSelectedId(null);
                setLookupTarget(null);
                setLookupEmployeeId(id);
                lookup.refresh();
              }}
            />
            <div className="panel-eyebrow">ВАШ ОФИС</div>
            <label className="office-picker">
              Офис
              <select
                value={active?.office_id ?? ""}
                onChange={(event) =>
                  selectFloor(
                    floors.find(
                      (floor) => floor.office_id === event.target.value,
                    )?.id ?? "",
                  )
                }
                disabled={!floors.length}
              >
                {offices.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <fieldset>
              <legend>Типы мест</legend>
              {(
                [
                  ["freedesk", "FreeDesk"],
                  ["dedicated", "Постоянные места"],
                  ["meeting", "Переговорные"],
                ] as const
              ).map(([key, label]) => (
                <label className="checkbox-label" key={key}>
                  <input
                    type="checkbox"
                    checked={filters[key]}
                    onChange={(event) => filter(key, event.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </fieldset>
            <label className="checkbox-label availability-filter">
              <input
                type="checkbox"
                checked={filters.availableOnly}
                onChange={(event) =>
                  filter("availableOnly", event.target.checked)
                }
              />
              Только свободные
            </label>
            <details className="map-help">
              <summary>Как пользоваться картой</summary>
              <p>
                Выберите дату и время. Нажмите на место, чтобы открыть детали.
              </p>
              <p>
                Перемещайте схему за свободную область. Масштаб меняется колесом
                и кнопками +/−. С клавиатуры: Tab и Enter для мест; стрелки и
                Home для схемы.
              </p>
            </details>
            <div className="filter-note">
              <Icon name="info" size={17} />
              <p>
                Статусы показывают брони на выбранное время, а не фактическое
                присутствие.
              </p>
            </div>
          </aside>
          <section className="map-panel" aria-label="Карта и выбор времени">
            <div className="period-controls">
              <label>
                <span>
                  <Icon name="layers" size={16} />
                  Этаж
                </span>
                <select
                  aria-label="Этаж"
                  value={floorId}
                  onChange={(event) => selectFloor(event.target.value)}
                  disabled={!floors.length}
                >
                  {floors
                    .filter((floor) => floor.office_id === active?.office_id)
                    .map((floor) => (
                      <option key={floor.id} value={floor.id}>
                        {floor.name}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                <span>
                  <Icon name="calendar" size={16} />
                  Дата
                </span>
                <input
                  aria-label="Дата"
                  type="date"
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                />
              </label>
              <label>
                <span>
                  <Icon name="clock" size={16} />
                  Начало
                </span>
                <input
                  aria-label="Начало"
                  type="time"
                  value={start}
                  step="1800"
                  onChange={(event) => setStart(event.target.value)}
                />
              </label>
              <label>
                <span>Окончание</span>
                <input
                  aria-label="Окончание"
                  type="time"
                  value={end}
                  step="1800"
                  onChange={(event) => setEnd(event.target.value)}
                />
              </label>
              <span className="time-zone">МСК</span>
            </div>
            <div className="time-presets" aria-label="Быстрый выбор времени">
              {PRESETS.map(([from, to]) => (
                <button
                  key={from}
                  aria-pressed={start === from && end === to}
                  onClick={() => {
                    setStart(from);
                    setEnd(to);
                  }}
                >
                  {from}–{to}
                </button>
              ))}
            </div>
            <div className="map-heading">
              <div>
                <h2>План этажа · Корпус А</h2>
                <p>
                  {active?.name ?? "Загрузка этажа"}
                  {window ? ` · ${moscowDate(window.from)}` : ""}
                </p>
              </div>
              <button
                className="icon-button"
                aria-label="Обновить доступность"
                onClick={refresh}
                disabled={status === "loading" || !window || !floorId}
              >
                <Icon name="refresh" size={19} />
              </button>
            </div>
            {snapshot && (
              <div className="map-statistics" aria-live="polite">
                <span>
                  <i className="free-dot" />
                  <strong>{freeDesks}</strong> рабочих мест свободно
                </span>
                <span>
                  <strong>
                    {
                      snapshot.items.filter(
                        (space) => space.kind === "MEETING_ROOM",
                      ).length
                    }
                  </strong>{" "}
                  переговорных
                </span>
                <span>{snapshot.items.length} ресурсов на этаже</span>
              </div>
            )}
            {!window ? (
              <div className="time-error" role="alert">
                <Icon name="clock" />
                Укажите дату и время: окончание должно быть позже начала.
              </div>
            ) : floorLoading ? (
              <StateCard title="Загружаем этажи…" busy />
            ) : floorError ? (
              <div role="alert">
                <StateCard
                  title="Не удалось загрузить офис"
                  action={
                    <button
                      className="secondary-button"
                      onClick={() => reloadFloors((value) => value + 1)}
                    >
                      Повторить загрузку
                    </button>
                  }
                >
                  {floorError}
                </StateCard>
              </div>
            ) : !floors.length ? (
              <StateCard title="Этажи пока не добавлены">
                Данные офиса появятся после настройки плана.
              </StateCard>
            ) : status === "loading" || status === "idle" ? (
              <StateCard title="Обновляем доступность…" busy>
                Проверяем выбранный период.
              </StateCard>
            ) : status === "error" ? (
              <div role="alert">
                <StateCard
                  title="Не удалось загрузить план"
                  action={
                    <button className="secondary-button" onClick={refresh}>
                      Повторить загрузку
                    </button>
                  }
                >
                  {error}
                </StateCard>
              </div>
            ) : !active || !planReady ? (
              <StateCard title="План этажа ещё не добавлен">
                Выберите другой этаж.
              </StateCard>
            ) : !snapshot?.items.length ? (
              <StateCard title="На этом этаже пока нет мест">
                Выберите другой этаж.
              </StateCard>
            ) : !visible.length ? (
              <StateCard
                title="Нет мест по выбранным фильтрам"
                action={
                  <button
                    className="secondary-button"
                    onClick={() => setFilters({ ...DEFAULT_FILTERS })}
                  >
                    Сбросить фильтры
                  </button>
                }
              >
                Попробуйте изменить типы мест или время.
              </StateCard>
            ) : (
              <>
                <FloorMap
                  key={active.id}
                  plan={active.plan}
                  spaces={visible}
                  selectedId={selectedId}
                  onSelect={selectSpace}
                />
                <label className="accessible-picker">
                  Место на плане
                  <select
                    value={selectedId ?? ""}
                    onChange={(event) =>
                      selectSpace(event.target.value || null)
                    }
                  >
                    <option value="">Выберите место</option>
                    {visible.map((space) => (
                      <option value={space.id} key={space.id}>
                        {space.id} · {STATUS_LABELS[statusOf(space)]}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}
            <Legend />
            <div className="map-update" aria-live="polite">
              {snapshot
                ? `Обновлено в ${moscowTime(snapshot.snapshot_at)} МСК · автообновление каждые 25 с`
                : "Доступность обновляется для выбранного периода"}
              <span>Демонстрационный план</span>
            </div>
          </section>
          <Details
            space={assistantProposal ? undefined : selected}
            floor={active}
            window={window}
            employeeId={session.employee.id}
            onClose={closeDetails}
            onBook={(space, floor, period) => {
              closeDetails();
              bookingFlow.begin(space, floor, period);
            }}
            lookup={lookup}
            lookupActive={Boolean(lookupEmployeeId && window)}
            onChooseLocation={(id) => {
              setLookupTarget(id);
              lookup.refresh();
            }}
            onShowAvailable={() => {
              closeDetails();
              setFilters({
                freedesk: true,
                dedicated: false,
                meeting: false,
                availableOnly: true,
              });
            }}
          />
        </div>
        <footer className="app-footer">{FOOTNOTE}</footer>
      </main>
    </>
  );
}

export function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined),
    [error, setError] = useState("");
  const [notice, setNotice] = useState(""),
    [retry, setRetry] = useState(0);
  const expired = useCallback(() => {
    setSession(null);
    setNotice("Сессия завершена. Войдите снова.");
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    api
      .me(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setSession(value);
      })
      .catch((reason) => {
        if (controller.signal.aborted) return;
        if (reason instanceof ApiError && reason.status === 401)
          setSession(null);
        else
          setError(
            reason instanceof Error
              ? reason.message
              : "Не удалось проверить сессию",
          );
      });
    return () => controller.abort();
  }, [retry]);
  const logout = async () => {
    if (!session) return;
    try {
      await api.logout(session.csrf_token);
      setSession(null);
      setNotice("");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) expired();
      else setNotice("Не удалось выйти. Повторите попытку.");
    }
  };
  if (session === undefined)
    return (
      <>
        <Header />
        <main className="startup-state">
          {error ? (
            <div role="alert">
              <StateCard
                title="Не удалось подключиться"
                action={
                  <button
                    className="primary-button"
                    onClick={() => setRetry((value) => value + 1)}
                  >
                    Повторить загрузку
                  </button>
                }
              >
                {error}
              </StateCard>
            </div>
          ) : (
            <StateCard title="Открываем Workspace…" busy />
          )}
        </main>
      </>
    );
  if (!session)
    return (
      <Login
        onLogin={(value) => {
          setSession(value);
          setNotice("");
        }}
        notice={notice}
      />
    );
  return (
    <Workspace
      session={session}
      onExpired={expired}
      onLogout={logout}
      notice={notice}
    />
  );
}
