import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent, PointerEvent } from "react";
import { Icon } from "./Icon";
import { SvgAvatar } from "./Avatar";
import { resourceLabel, statusOf } from "./domain";
import type { Plan, Space } from "./types";

type View = { scale: number; x: number; y: number };
const FIT: View = { scale: 1, x: 0, y: 0 };
const clamp = (value: number, min: number, max: number) =>
  Math.max(min, Math.min(max, value));
function bound(view: View, plan: Plan): View {
  return {
    ...view,
    x: clamp(view.x, -plan.width * (view.scale - 0.9), plan.width * 0.1),
    y: clamp(view.y, -plan.height * (view.scale - 0.9), plan.height * 0.1),
  };
}
function zoom(
  view: View,
  factor: number,
  x: number,
  y: number,
  plan: Plan,
): View {
  const scale = clamp(view.scale * factor, 1, 3);
  const ratio = scale / view.scale;
  return bound(
    { scale, x: x - (x - view.x) * ratio, y: y - (y - view.y) * ratio },
    plan,
  );
}
function point(svg: SVGSVGElement, x: number, y: number, plan: Plan) {
  const matrix = svg.getScreenCTM?.();
  if (matrix && typeof DOMPoint !== "undefined")
    return new DOMPoint(x, y).matrixTransform(matrix.inverse());
  const rect = svg.getBoundingClientRect();
  return {
    x: ((x - rect.left) * plan.width) / (rect.width || plan.width),
    y: ((y - rect.top) * plan.height) / (rect.height || plan.height),
  };
}

export function FloorMap({
  plan,
  spaces,
  selectedId,
  onSelect,
}: {
  plan: Plan;
  spaces: Space[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [view, setView] = useState<View>(FIT);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{
    pointer: number;
    x: number;
    y: number;
    view: View;
  } | null>(null);
  const pattern = useId().replaceAll(":", "");
  useEffect(() => {
    const node = svg.current;
    if (!node) return;
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      const anchor = point(node, event.clientX, event.clientY, plan);
      setView((previous) =>
        zoom(
          previous,
          event.deltaY < 0 ? 1.12 : 1 / 1.12,
          anchor.x,
          anchor.y,
          plan,
        ),
      );
    };
    node.addEventListener("wheel", wheel, { passive: false });
    return () => node.removeEventListener("wheel", wheel);
  }, [plan]);

  function panStart(event: PointerEvent<SVGSVGElement>) {
    if (
      event.button !== 0 ||
      (event.target as Element).closest("[data-resource]")
    )
      return;
    const anchor = point(
      event.currentTarget,
      event.clientX,
      event.clientY,
      plan,
    );
    drag.current = { pointer: event.pointerId, x: anchor.x, y: anchor.y, view };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function panMove(event: PointerEvent<SVGSVGElement>) {
    const start = drag.current;
    if (!start || start.pointer !== event.pointerId) return;
    const anchor = point(
      event.currentTarget,
      event.clientX,
      event.clientY,
      plan,
    );
    setView(
      bound(
        {
          ...start.view,
          x: start.view.x + anchor.x - start.x,
          y: start.view.y + anchor.y - start.y,
        },
        plan,
      ),
    );
  }
  function panEnd(event: PointerEvent<SVGSVGElement>) {
    drag.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId))
      event.currentTarget.releasePointerCapture(event.pointerId);
  }
  function keyboard(event: KeyboardEvent<SVGSVGElement>) {
    if (event.target !== event.currentTarget) return;
    const deltas: Record<string, [number, number]> = {
      ArrowLeft: [40, 0],
      ArrowRight: [-40, 0],
      ArrowUp: [0, 40],
      ArrowDown: [0, -40],
    };
    if (deltas[event.key]) {
      event.preventDefault();
      const [x, y] = deltas[event.key];
      setView((previous) =>
        bound({ ...previous, x: previous.x + x, y: previous.y + y }, plan),
      );
    }
    if (event.key === "Home") {
      event.preventDefault();
      setView(FIT);
    }
  }
  const changeZoom = (factor: number) =>
    setView((previous) =>
      zoom(previous, factor, plan.width / 2, plan.height / 2, plan),
    );

  return (
    <>
      <div
        className="map-viewport"
        data-testid="map-viewport"
        data-scale={view.scale}
      >
        <div className="map-caption">
          <span className="map-dot" /> Схема этажа{" "}
          <span className="scale-value" aria-label="Масштаб">
            {Math.round(view.scale * 100)}%
          </span>
        </div>
        <svg
          ref={svg}
          viewBox={`0 0 ${plan.width} ${plan.height}`}
          role="group"
          aria-label="Интерактивный план этажа"
          tabIndex={0}
          onPointerDown={panStart}
          onPointerMove={panMove}
          onPointerUp={panEnd}
          onPointerCancel={panEnd}
          onKeyDown={keyboard}
        >
          <defs>
            <pattern
              id={pattern}
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="2" cy="2" r=".7" fill="var(--map-dots)" />
            </pattern>
          </defs>
          <rect
            width={plan.width}
            height={plan.height}
            fill={`url(#${pattern})`}
          />
          <g
            data-testid="map-transform"
            transform={`translate(${view.x} ${view.y}) scale(${view.scale})`}
          >
            <rect {...plan.outline} rx="7" className="floor-outline" />
            {plan.zones.map((zone) => (
              <g
                key={zone.id}
                aria-label={zone.label}
                className={`plan-zone zone-${zone.kind}`}
              >
                <rect
                  x={zone.x}
                  y={zone.y}
                  width={zone.width}
                  height={zone.height}
                />
                <text
                  x={zone.x + zone.width / 2}
                  y={zone.y + zone.height / 2 - (zone.note ? 6 : 0)}
                  textAnchor="middle"
                >
                  {zone.label}
                </text>
                {zone.note && (
                  <text
                    className="zone-note"
                    x={zone.x + zone.width / 2}
                    y={zone.y + zone.height / 2 + 16}
                    textAnchor="middle"
                  >
                    {zone.note}
                  </text>
                )}
              </g>
            ))}
            {plan.walls.map((wall, index) => (
              <line key={`wall-${index}`} {...wall} className="plan-wall" />
            ))}
            {plan.windows.map((window, index) => (
              <line
                key={`window-${index}`}
                {...window}
                className="plan-window"
              />
            ))}
            {plan.doors.map((door, index) => (
              <g
                key={`door-${index}`}
                transform={`translate(${door.x} ${door.y})${door.vertical ? " rotate(90)" : ""}`}
                className="plan-door"
              >
                <line
                  x1="0"
                  y1="0"
                  x2={door.size}
                  y2="0"
                  className="door-gap"
                />
                <path
                  d={`M0 0 V${-door.size} A${door.size} ${door.size} 0 0 1 ${door.size} 0`}
                />
              </g>
            ))}
            {plan.hvac.map((unit, index) => (
              <g
                key={`hvac-${index}`}
                className="plan-hvac"
                aria-label="Вентиляция"
              >
                <rect {...unit} rx="4" />
                <path
                  d={`M${unit.x + 5} ${unit.y + 5}h${unit.width - 10}m${-(unit.width - 10)} 5h${unit.width - 10}`}
                />
              </g>
            ))}
            {plan.plants.map((plant, index) => (
              <g key={`plant-${index}`} className="plan-plant">
                <circle {...{ cx: plant.x, cy: plant.y }} r="12" />
                <path d={`M${plant.x - 4} ${plant.y + 5}l8-10m-8 3l8 4`} />
              </g>
            ))}
            {spaces.map((space) => {
              const { x, y, width, height, label } = space.layout;
              const status = statusOf(space),
                room = space.kind === "MEETING_ROOM",
                selected = space.id === selectedId;
              const people =
                room || status === "free"
                  ? []
                  : (status === "dedicated"
                      ? space.assignments
                      : space.reservations
                    ).flatMap((row) =>
                      row.person_public ? [row.person_public] : [],
                    );
              return (
                <g
                  key={space.id}
                  transform={`translate(${x} ${y})`}
                  data-resource={space.id}
                  data-testid={`space-${space.id}`}
                  data-status={status}
                  className={`map-space status-${status}${selected ? " is-selected" : ""}${room ? " meeting-space" : ""}`}
                  role="button"
                  tabIndex={0}
                  aria-label={resourceLabel(space)}
                  aria-pressed={selected}
                  onClick={() => onSelect(space.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      event.stopPropagation();
                      onSelect(space.id);
                    }
                  }}
                >
                  <title>{resourceLabel(space)}</title>
                  {selected && (
                    <rect
                      className="selection-ring"
                      x="-6"
                      y={room ? -6 : people.length ? -34 : -20}
                      width={width + 12}
                      height={height + (room ? 12 : people.length ? 42 : 28)}
                      rx="11"
                    />
                  )}
                  {!room && (
                    <rect
                      className="desk-chair"
                      x={width * 0.22}
                      y="-13"
                      width={width * 0.56}
                      height="8"
                      rx="3"
                    />
                  )}
                  <rect
                    className="space-body"
                    width={width}
                    height={height}
                    rx={room ? 9 : 7}
                  />
                  <text
                    x={width / 2}
                    y={room ? height / 2 - 13 : height / 2 + 4}
                    textAnchor="middle"
                    className="space-id"
                  >
                    {space.id}
                  </text>
                  {room && (
                    <>
                      <text
                        x={width / 2}
                        y={height / 2 + 9}
                        textAnchor="middle"
                        className="room-name"
                      >
                        {label ?? "Переговорная"}
                      </text>
                      <text
                        x={width / 2}
                        y={height / 2 + 30}
                        textAnchor="middle"
                        className="room-capacity"
                      >
                        {space.capacity} мест
                      </text>
                    </>
                  )}
                  {people.slice(0, 2).map((person, index) => (
                    <SvgAvatar
                      key={`${person.id}-${index}`}
                      person={person}
                      x={width / 2 - (people.length > 1 ? 27 : 17) + index * 20}
                      y={-27}
                    />
                  ))}
                  <g
                    transform={`translate(${width - 8} ${room ? 12 : 1})`}
                    className="resource-marker"
                  >
                    <circle r="9" />
                    {status === "dedicated" ? (
                      <g transform="translate(-6 -6)">
                        <Icon name="lock" size={12} />
                      </g>
                    ) : (
                      <text textAnchor="middle" y="3.5">
                        {status === "mine"
                          ? "✓"
                          : space.reservations.length > 1
                            ? space.reservations.length
                            : status === "booked"
                              ? "—"
                              : "✓"}
                      </text>
                    )}
                  </g>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
      <div className="zoom-controls" aria-label="Управление картой">
        <button
          className="icon-button"
          aria-label="Увеличить масштаб"
          onClick={() => changeZoom(1.25)}
          disabled={view.scale >= 3}
        >
          <Icon name="plus" />
        </button>
        <button
          className="icon-button"
          aria-label="Уменьшить масштаб"
          onClick={() => changeZoom(0.8)}
          disabled={view.scale <= 1}
        >
          <Icon name="minus" />
        </button>
        <button
          className="icon-button"
          aria-label="Показать весь этаж"
          onClick={() => setView(FIT)}
        >
          <Icon name="fit" />
        </button>
      </div>
    </>
  );
}
