import { fireEvent, render, screen } from "@testing-library/react";
import { Avatar } from "./Avatar";
import type { PersonPublic } from "./types";

const maria: PersonPublic = {
  id: "e03",
  full_name: "Мария Соколова",
  job_title: "Научный сотрудник",
  department: "Лаборатория",
  fictional: true,
};

describe("fictional avatars", () => {
  it("has accessible initials when no approved image exists", () => {
    render(<Avatar person={maria} />);
    expect(
      screen.getByRole("img", { name: /Мария Соколова, вымышленный профиль/ }),
    ).toHaveTextContent("МС");
  });
  it("falls back on image failure and does not carry that failure to another person", () => {
    const { container, rerender } = render(
      <Avatar person={{ ...maria, avatar_url: "/demo-avatars/v1/e03.svg" }} />,
    );
    fireEvent.error(container.querySelector("img")!);
    expect(screen.getByText("МС")).toBeInTheDocument();
    rerender(
      <Avatar
        person={{
          ...maria,
          id: "e04",
          full_name: "Павел Громов",
          avatar_url: "/demo-avatars/v1/e04.svg",
        }}
      />,
    );
    expect(container.querySelector("img")).toHaveAttribute(
      "src",
      "/demo-avatars/v1/e04.svg",
    );
    expect(screen.queryByText("МС")).not.toBeInTheDocument();
  });
});
