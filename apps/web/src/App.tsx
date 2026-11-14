import { useEffect, useState } from "react";

type Status = "loading" | "ok" | "down";

// WB-01: proves the web container can reach both backends through the proxy.
// The interactive floor map belongs to WB-03.
export function App() {
  const [booking, setBooking] = useState<Status>("loading");
  const [assistant, setAssistant] = useState<Status>("loading");

  useEffect(() => {
    const probe = (url: string, set: (s: Status) => void) =>
      fetch(url)
        .then((r) => set(r.ok ? "ok" : "down"))
        .catch(() => set("down"));
    probe("/api/v1/healthz", setBooking);
    probe("/api/v1/assistant/healthz", setAssistant);
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <span className="brand">BIOCAD Workspace</span>
        <span className="muted">Бронирование рабочих мест и переговорных</span>
      </header>
      <section className="card" aria-label="Состояние сервисов">
        <h1>Каркас приложения</h1>
        <ul>
          <li data-testid="booking-status">Booking Service: {booking}</li>
          <li data-testid="assistant-status">Assistant Service: {assistant}</li>
        </ul>
        <p className="muted">
          Цвета — приближённые токены BIOCAD, не официальный UI Kit. Все данные демо и вымышлены.
        </p>
      </section>
    </main>
  );
}
