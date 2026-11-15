import { useRef, useState } from "react";
import { Avatar } from "./Avatar";
import { Icon } from "./Icon";
import type { TimeWindow } from "./types";
import { useEmployeeSearch } from "./useEmployees";

export function EmployeeSearch({
  window,
  selectedId,
  onSelect,
  onExpired,
  revision = 0,
}: {
  window: TimeWindow | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onExpired: () => void;
  revision?: number;
}) {
  const [open, setOpen] = useState(
    () =>
      typeof matchMedia === "undefined" ||
      !matchMedia("(max-width: 820px)").matches,
  );
  const [query, setQuery] = useState("");
  const toggle = useRef<HTMLButtonElement>(null);
  const { data, status, error, refresh } = useEmployeeSearch(
    query,
    open ? window : null,
    onExpired,
    revision,
  );
  return (
    <section className="employee-search" aria-label="Поиск сотрудников">
      <button
        ref={toggle}
        className="employee-search-toggle"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <Icon name="search" size={16} />
        <strong>Найти сотрудника</strong>
        <span aria-hidden="true">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="employee-search-content">
          <label className="employee-search-field">
            <span className="sr-only">ФИО или отдел сотрудника</span>
            <input
              type="search"
              value={query}
              maxLength={80}
              placeholder="ФИО или отдел"
              disabled={!window}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <div className="employee-search-status" aria-live="polite">
            {!window
              ? "Выберите корректный интервал"
              : status === "loading"
                ? "Ищем сотрудников…"
                : status === "ready"
                  ? `Найдено: ${data?.items.length ?? 0}`
                  : ""}
          </div>
          {status === "error" ? (
            <div className="employee-search-error" role="alert">
              <p>{error}</p>
              <button className="text-button" onClick={refresh}>
                Повторить поиск
              </button>
            </div>
          ) : status === "ready" && data?.items.length === 0 ? (
            <p className="employee-empty">
              Сотрудники не найдены. Попробуйте другое имя или отдел.
            </p>
          ) : (
            <ul
              className="employee-results"
              aria-label="Результаты поиска сотрудников"
            >
              {data?.items.map((person) => {
                const first = person.locations?.[0];
                return (
                  <li key={person.id}>
                    <button
                      className={`employee-result${selectedId === person.id ? " is-selected" : ""}`}
                      aria-label={`Показать сотрудника ${person.full_name}`}
                      aria-pressed={selectedId === person.id}
                      onClick={() => {
                        onSelect(person.id);
                        if (
                          typeof matchMedia !== "undefined" &&
                          matchMedia("(max-width: 820px)").matches
                        ) {
                          setOpen(false);
                          toggle.current?.focus();
                        }
                      }}
                    >
                      <Avatar person={person} size={34} />
                      <span className="employee-result-info">
                        <strong>{person.full_name}</strong>
                        <small>
                          {person.job_title} · {person.department}
                        </small>
                        <span>
                          {first
                            ? `${first.floor_number} этаж · ${first.space_id}${(person.locations?.length ?? 0) > 1 ? ` · ещё ${(person.locations?.length ?? 1) - 1}` : ""}`
                            : "Нет брони или закрепления"}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          <p className="employee-search-note">
            Брони и закрепления на выбранное время. Профили и иллюстрации
            вымышлены.
          </p>
        </div>
      )}
    </section>
  );
}
