import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "./api";
import { Dialog } from "./BookingFlow";
import { moscowDate, moscowTime } from "./domain";
import type {
  AssistantProposal,
  ChatMessage,
  Floor,
  Session,
  TimeWindow,
} from "./types";

export function ProposalSummary({ proposal }: { proposal: AssistantProposal }) {
  return (
    <div className="booking-summary">
      <strong>{proposal.selection.space_id}</strong>
      <p>{proposal.space.kind === "MEETING_ROOM" ? `Переговорная · до ${proposal.space.capacity} человек` : "FreeDesk · рабочее место"}</p>
      <p>
        {proposal.floor.office_name} · {proposal.floor.name}
      </p>
      <p>
        {moscowDate(proposal.selection.start_at)} ·{" "}
        {moscowTime(proposal.selection.start_at)}–
        {moscowTime(proposal.selection.end_at)} МСК
      </p>
      <p>Предложение AI. Бронь ещё не создана.</p>
    </div>
  );
}

export function AssistantChat({
  session,
  floor,
  floors,
  window,
  close,
  onExpired,
  onProposal,
}: {
  session: Session;
  floor: Floor;
  floors: Floor[];
  window: TimeWindow;
  close: () => void;
  onExpired: () => void;
  onProposal: (value: AssistantProposal) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [proposal, setProposal] = useState<AssistantProposal | null>(null);
  const controller = useRef<AbortController | null>(null);
  const locked = useRef(false);
  useEffect(() => () => controller.current?.abort(), []);
  const send = async (event: FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || !consent || locked.current) return;
    locked.current = true;
    setBusy(true);
    setError("");
    setProposal(null);
    const pending: ChatMessage = { role: "user", content: text };
    setMessages([...messages, pending]);
    setInput("");
    const request = new AbortController();
    controller.current = request;
    try {
      const result = await api.chat(
        text,
        messages.slice(-6),
        {
          floor_id: floor.id,
          start_at: window.from,
          end_at: window.to,
          floors: floors.map(({ id, name, number }) => ({ id, name, number })),
        },
        session.csrf_token,
        request.signal,
      );
      if (request.signal.aborted) return;
      setMessages([
        ...messages,
        pending,
        { role: "assistant", content: result.reply },
      ]);
      setProposal(result.proposal);
      if (result.proposal) onProposal(result.proposal);
    } catch (reason) {
      if (request.signal.aborted) return;
      if (reason instanceof ApiError && reason.status === 401) onExpired();
      else
        setError(
          reason instanceof Error
            ? reason.message
            : "AI недоступен. Используйте форму.",
        );
    } finally {
      locked.current = false;
      if (!request.signal.aborted) setBusy(false);
    }
  };
  return (
    <Dialog title="AI-ассистент" close={close}>
      <p className="muted">
        Найду FreeDesk или переговорную по актуальной доступности. Бронируете
        вы, после проверки точного места и времени.
      </p>
      <p>
        Выбрано на плане: {floor.name} · {moscowDate(window.from)} ·{" "}
        {moscowTime(window.from)}–{moscowTime(window.to)} МСК.
      </p>
      <div
        className="assistant-messages"
        role="log"
        aria-label="Переписка с ассистентом"
        aria-live="polite"
      >
        {messages.map((message, index) => (
          <p key={index} className={`assistant-message ${message.role}`}>
            <strong>{message.role === "user" ? "Вы" : "Ассистент"}: </strong>
            {message.content}
          </p>
        ))}
      </div>
      {proposal && (
        <>
          <ProposalSummary proposal={proposal} />
          <button className="primary-button" onClick={close}>
            Показать предложение на плане
          </button>
        </>
      )}
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {busy && (
        <p role="status">
          Проверяем доступность… Можно закрыть чат и использовать форму.
        </p>
      )}
      <form onSubmit={send} className="assistant-form">
        <label className="assistant-consent">
          <input
            type="checkbox"
            checked={consent}
            onChange={(event) => setConsent(event.target.checked)}
            disabled={busy}
          />
          Разрешаю отправить текст запроса и вымышленные демо-профили в
          OpenRouter. Не указывайте персональные данные или секреты.
        </label>
        <label>
          Запрос ассистенту
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            maxLength={1500}
            rows={3}
            disabled={busy}
            placeholder="Найди переговорную на 6 человек 16 ноября с 14 до 15"
          />
        </label>
        <div className="booking-actions">
          <button type="button" className="secondary-button" onClick={close}>
            Вернуться к плану
          </button>
          <button
            className="primary-button"
            disabled={!consent || !input.trim() || busy}
          >
            Отправить
          </button>
        </div>
      </form>
    </Dialog>
  );
}
