import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Button } from "../components/common/Button";
import { Breadcrumbs } from "../components/files/Breadcrumbs";
import { ErrorMessage } from "../components/common/ErrorMessage";
import { EmptyState } from "../components/files/EmptyState";

describe("Button component", () => {
  it("renders children and handles click", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    const btn = screen.getByRole("button", { name: /click me/i });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("disables button when loading", () => {
    render(<Button isLoading>Submit</Button>);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
  });
});

describe("ErrorMessage component", () => {
  it("renders error message and code", () => {
    render(
      <ErrorMessage message="Access forbidden." code="PERMISSION_DENIED" />,
    );
    expect(screen.getByText("Access forbidden.")).toBeInTheDocument();
    expect(
      screen.getByText(/error code: permission_denied/i),
    ).toBeInTheDocument();
  });

  it("renders null if no message", () => {
    const { container } = render(<ErrorMessage message={null} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("Breadcrumbs component", () => {
  it("renders root link", () => {
    render(
      <BrowserRouter>
        <Breadcrumbs />
      </BrowserRouter>,
    );
    expect(screen.getByText("My Files")).toBeInTheDocument();
  });

  it("renders folder name when in subfolder", () => {
    render(
      <BrowserRouter>
        <Breadcrumbs
          currentFolder={{
            id: 1,
            name: "University",
            owner_id: 1,
            created_at: "",
            updated_at: "",
          }}
        />
      </BrowserRouter>,
    );
    expect(screen.getByText("My Files")).toBeInTheDocument();
    expect(screen.getByText("University")).toBeInTheDocument();
  });
});

describe("EmptyState component", () => {
  it("triggers upload and new folder actions", () => {
    const onUpload = vi.fn();
    const onCreateFolder = vi.fn();
    render(
      <EmptyState
        onUploadClick={onUpload}
        onCreateFolderClick={onCreateFolder}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /upload files/i }));
    expect(onUpload).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /new folder/i }));
    expect(onCreateFolder).toHaveBeenCalledTimes(1);
  });
});
