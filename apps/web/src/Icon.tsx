const paths = {
  map: "M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2V5zm6-2v16m6-14v16",
  pin: "M20 10c0 6-8 11-8 11S4 16 4 10a8 8 0 1116 0zM12 7a3 3 0 100 6 3 3 0 000-6z",
  calendar: "M4 5h16v16H4V5zm3-3v6m10-6v6M4 10h16",
  clock: "M12 3a9 9 0 100 18 9 9 0 000-18zm0 4v5l4 2",
  lock: "M6 10h12v11H6V10zm2 0V6a4 4 0 018 0v4m-4 5v2",
  close: "M6 6l12 12M18 6L6 18",
  logout: "M9 4H4v16h5m5-12l4 4-4 4m-6-4h10",
  refresh:
    "M20 7v5h-5M4 17v-5h5m10-5a8 8 0 00-13-2L4 8m16 8l-2 3a8 8 0 01-13-2",
  plus: "M12 5v14M5 12h14",
  minus: "M5 12h14",
  fit: "M3 9V3h6m6 0h6v6m0 6v6h-6m-6 0H3v-6",
  check: "M5 12l4 4L19 6",
  info: "M12 3a9 9 0 100 18 9 9 0 000-18zm0 7v7m0-11v1",
  arrow: "M5 12h14m-5-5l5 5-5 5",
  layers: "M12 3L2 8l10 5 10-5-10-5zM2 12l10 5 10-5M2 16l10 5 10-5",
};
export function Icon({
  name,
  size = 20,
}: {
  name: keyof typeof paths;
  size?: number;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}
