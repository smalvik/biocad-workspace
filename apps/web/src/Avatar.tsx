import { useState } from "react";
import { initials } from "./domain";
import type { PersonPublic } from "./types";

export function Avatar({
  person,
  size = 40,
  className = "",
}: {
  person: PersonPublic;
  size?: number;
  className?: string;
}) {
  const [failed, setFailed] = useState<string | null>(null);
  const source = person.avatar_url;
  return (
    <span
      className={`person-avatar ${className}`}
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Аватар: ${person.full_name}${person.fictional ? ", вымышленный профиль" : ""}`}
      data-person-id={person.id}
    >
      {source && source !== failed ? (
        <img
          src={source}
          alt=""
          onError={() => setFailed(source)}
          decoding="async"
        />
      ) : (
        <span className="avatar-initials">
          {initials(person.full_name) || "?"}
        </span>
      )}
    </span>
  );
}

export function SvgAvatar({
  person,
  x,
  y,
  size = 34,
}: {
  person: PersonPublic;
  x: number;
  y: number;
  size?: number;
}) {
  const [failed, setFailed] = useState<string | null>(null);
  const source = person.avatar_url;
  return (
    <g
      transform={`translate(${x} ${y})`}
      data-person-id={person.id}
      aria-hidden="true"
      className="map-avatar"
    >
      <circle cx={size / 2} cy={size / 2} r={size / 2 + 1} />
      {source && source !== failed ? (
        <image
          href={source}
          width={size}
          height={size}
          onError={() => setFailed(source)}
        />
      ) : (
        <text
          x={size / 2}
          y={size / 2 + 4}
          textAnchor="middle"
          className="map-avatar-initials"
        >
          {initials(person.full_name) || "?"}
        </text>
      )}
    </g>
  );
}

export function PersonSummary({
  person,
  compact = false,
}: {
  person: PersonPublic;
  compact?: boolean;
}) {
  return (
    <div className={`person-summary${compact ? " is-compact" : ""}`}>
      <Avatar person={person} size={compact ? 32 : 44} />
      <div>
        <strong>{person.full_name}</strong>
        <span>{person.job_title}</span>
        <small>{person.department}</small>
      </div>
    </div>
  );
}
