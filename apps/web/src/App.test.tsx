import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import { api, ApiError } from "./api";
import type { Floor, Session, Snapshot, Space } from "./types";

const session: Session = {
  employee: {
    id: "e01",
    full_name: "Анна Смирнова",
    job_title: "Научный сотрудник",
    department: "R&D",
    fictional: true,
  },
  csrf_token: "fictional-csrf-for-unit-test",
};
const floor: Floor = {
  id: "floor-2",
  number: 2,
  name: "Этаж 2",
  office_id: "moscow-a",
  office_name: "Москва, Корпус А",
  plan: {
    width: 1100,
    height: 720,
    outline: { x: 40, y: 40, width: 1020, height: 640 },
    zones: [],
    doors: [],
    walls: [],
    windows: [],
    hvac: [],
    plants: [],
  },
};
const space: Space = {
  id: "D-03",
  floor_id: "floor-2",
  kind: "DESK",
  desk_mode: "FREEDESK",
  capacity: 1,
  zone: "open-space",
  layout: { x: 100, y: 100, width: 66, height: 48 },
  is_available_for_full_interval: true,
  is_partial: false,
  reservations: [],
  assignments: [],
};
function fixtures() {
  vi.spyOn(api, "floors").mockResolvedValue({ items: [floor] });
  vi.spyOn(api, "snapshot").mockImplementation(
    async (id, window): Promise<Snapshot> => ({
      floor_id: id,
      ...window,
      snapshot_at: "2026-11-14T12:00:00Z",
      items: [space],
    }),
  );
}
afterEach(() => vi.restoreAllMocks());

describe("authenticated office map", () => {
  it("requires explicit demo login and opens the actual map flow", async () => {
    vi.spyOn(api, "me").mockRejectedValue(new ApiError("Войдите", 401));
    const login = vi.spyOn(api, "login").mockResolvedValue(session);
    fixtures();
    render(<App />);
    await screen.findByRole("heading", { name: "Войти в Workspace" });
    fireEvent.change(screen.getByLabelText("Пароль"), {
      target: { value: "demo-workspace" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Войти" }));
    await screen.findByTestId("space-D-03");
    expect(login).toHaveBeenCalledWith("e01", "demo-workspace");
    expect(
      screen.getByRole("group", { name: "Интерактивный план этажа" }),
    ).toBeInTheDocument();
    fireEvent.keyDown(screen.getByTestId("space-D-03"), { key: "Enter" });
    expect(
      screen.getByRole("heading", { name: "FreeDesk D-03" }),
    ).toBeInTheDocument();
  });
  it("shows a useful empty state and restores filters", async () => {
    vi.spyOn(api, "me").mockResolvedValue(session);
    fixtures();
    render(<App />);
    await screen.findByTestId("space-D-03");
    fireEvent.click(screen.getByLabelText("FreeDesk"));
    expect(
      screen.getByRole("heading", { name: "Нет мест по выбранным фильтрам" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Сбросить фильтры" }));
    expect(screen.getByTestId("space-D-03")).toBeInTheDocument();
  });
  it("reports a failed snapshot and retries without inventing availability", async () => {
    vi.spyOn(api, "me").mockResolvedValue(session);
    fixtures();
    vi.mocked(api.snapshot).mockRejectedValueOnce(
      new ApiError("Сервис временно недоступен", 503),
    );
    render(<App />);
    await screen.findByRole("heading", { name: "Не удалось загрузить план" });
    expect(screen.queryByTestId("space-D-03")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Повторить загрузку" }));
    await screen.findByTestId("space-D-03");
  });
  it("does not fetch an invalid time window or show a prior snapshot as free", async () => {
    vi.spyOn(api, "me").mockResolvedValue(session);
    fixtures();
    render(<App />);
    await screen.findByTestId("space-D-03");
    const count = vi.mocked(api.snapshot).mock.calls.length;
    fireEvent.change(screen.getByLabelText("Окончание"), {
      target: { value: "09:00" },
    });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "окончание должно быть позже начала",
    );
    expect(screen.queryByTestId("space-D-03")).not.toBeInTheDocument();
    await waitFor(() => expect(api.snapshot).toHaveBeenCalledTimes(count));
  });
});
