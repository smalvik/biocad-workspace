import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { App } from "./App";
import { api, ApiError } from "./api";
import type {
  EmployeeLocationResponse,
  Floor,
  Session,
  Snapshot,
  Space,
} from "./types";

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
  vi.spyOn(api, "employees").mockImplementation(async (_, window) => ({
    ...window,
    snapshot_at: "2026-11-14T12:00:00Z",
    items: [],
  }));
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
  it("locates an employee on another floor and resets filters which would hide the reservation", async () => {
    vi.spyOn(api, "me").mockResolvedValue(session);
    fixtures();
    const third = { ...floor, id: "floor-3", number: 3, name: "Этаж 3" };
    const person = {
      ...session.employee,
      id: "e12",
      full_name: "Максим Николаев",
    };
    const location = {
      relation: "reservation" as const,
      space_id: "D-32",
      space_kind: "DESK" as const,
      desk_mode: "FREEDESK" as const,
      floor_id: "floor-3",
      floor_number: 3,
      floor_name: "Этаж 3",
      office_id: "moscow-a",
      office_name: floor.office_name,
      start_at: "2026-11-16T10:00:00+03:00",
      end_at: "2026-11-16T12:00:00+03:00",
    };
    vi.mocked(api.floors).mockResolvedValue({ items: [floor, third] });
    vi.mocked(api.snapshot).mockImplementation(async (id, window) => ({
      ...window,
      floor_id: id,
      snapshot_at: "2026-11-14T12:00:00Z",
      items: [
        {
          ...space,
          id: id === "floor-3" ? "D-32" : "D-03",
          floor_id: id,
          is_available_for_full_interval: false,
        },
      ],
    }));
    vi.mocked(api.employees).mockImplementation(async (_, window) => ({
      ...window,
      snapshot_at: "2026-11-14T12:00:00Z",
      items: [{ ...person, locations: [location] }],
    }));
    vi.spyOn(api, "employeeLocation").mockImplementation(async (_, window) => ({
      ...window,
      snapshot_at: "2026-11-14T12:00:00Z",
      employee: person,
      locations: [location],
    }));
    render(<App />);
    await screen.findByTestId("space-D-03");
    fireEvent.click(screen.getByLabelText("Только свободные"));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Показать сотрудника Максим Николаев",
      }),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Этаж")).toHaveValue("floor-3"),
    );
    await waitFor(() =>
      expect(screen.getByTestId("space-D-32")).toHaveAttribute(
        "aria-pressed",
        "true",
      ),
    );
    expect(screen.getByLabelText("Только свободные")).not.toBeChecked();
    expect(
      screen.getByRole("heading", { name: "FreeDesk D-32" }),
    ).toBeInTheDocument();
  });
  it("does not let a late employee lookup override a later manual map selection", async () => {
    vi.spyOn(api, "me").mockResolvedValue(session);
    fixtures();
    vi.mocked(api.employees).mockImplementation(async (_, window) => ({
      ...window,
      snapshot_at: "2026-11-14T12:00:00Z",
      items: [{ ...session.employee, locations: [] }],
    }));
    let resolve!: (value: EmployeeLocationResponse) => void;
    vi.spyOn(api, "employeeLocation").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    render(<App />);
    await screen.findByTestId("space-D-03");
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Показать сотрудника Анна Смирнова",
      }),
    );
    await waitFor(() => expect(api.employeeLocation).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByTestId("space-D-03"));
    await act(async () =>
      resolve({
        from: "2026-11-16T10:00:00+03:00",
        to: "2026-11-16T12:00:00+03:00",
        snapshot_at: "2026-11-14T12:00:00Z",
        employee: session.employee,
        locations: [],
      }),
    );
    expect(
      screen.getByRole("heading", { name: "FreeDesk D-03" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "Брони или закрепления на выбранный интервал не найдены.",
      ),
    ).not.toBeInTheDocument();
  });
});
