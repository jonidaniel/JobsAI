import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { downloadBlob } from "../fileDownload";

describe("downloadBlob", () => {
  let mockCreateObjectURL;
  let mockRevokeObjectURL;
  let mockAppendChild;
  let mockRemoveChild;
  let mockClick;

  beforeEach(() => {
    // Mock URL.createObjectURL and revokeObjectURL
    mockCreateObjectURL = vi.fn(() => "blob:mock-url");
    mockRevokeObjectURL = vi.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock DOM methods
    mockClick = vi.fn();
    mockAppendChild = vi.fn();
    mockRemoveChild = vi.fn();

    // Create mock anchor element
    const mockAnchor = {
      href: "",
      download: "",
      style: {},
      setAttribute: vi.fn(),
      click: mockClick,
    };

    // Mock document.createElement
    vi.spyOn(document, "createElement").mockReturnValue(mockAnchor);
    vi.spyOn(document.body, "appendChild").mockImplementation(mockAppendChild);
    vi.spyOn(document.body, "removeChild").mockImplementation(mockRemoveChild);

    // Mock window.scrollY
    Object.defineProperty(window, "scrollY", {
      writable: true,
      configurable: true,
      value: 100,
    });
    Object.defineProperty(window, "pageYOffset", {
      writable: true,
      configurable: true,
      value: 100,
    });

    // Mock requestAnimationFrame
    global.requestAnimationFrame = vi.fn((cb) => {
      cb();
      return 1;
    });
    global.window.scrollTo = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should download blob with default filename when no filename provided", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    downloadBlob(blob, headers);

    expect(mockCreateObjectURL).toHaveBeenCalledWith(blob);
    expect(document.createElement).toHaveBeenCalledWith("a");
    const anchor = document.createElement("a");
    expect(anchor.download).toBe("document.docx");
    expect(mockClick).toHaveBeenCalled();
    expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
  });

  it("should use provided defaultFilename", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    downloadBlob(blob, headers, "cover_letter.docx");

    const anchor = document.createElement("a");
    expect(anchor.download).toBe("cover_letter.docx");
  });

  it("should extract filename from Content-Disposition header when defaultFilename is generic", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();
    headers.set("Content-Disposition", 'filename="test_file.docx"');

    downloadBlob(blob, headers, "document.docx");

    const anchor = document.createElement("a");
    expect(anchor.download).toBe("test_file.docx");
  });

  it("should prioritize defaultFilename over header when defaultFilename is not generic", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();
    headers.set("Content-Disposition", 'filename="header_file.docx"');

    downloadBlob(blob, headers, "cover_letter.docx");

    const anchor = document.createElement("a");
    expect(anchor.download).toBe("cover_letter.docx");
  });

  it("should handle RFC 5987 encoded filename in Content-Disposition", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();
    headers.set("Content-Disposition", "filename*=UTF-8''test%20file.docx");

    downloadBlob(blob, headers, "document.docx");

    const anchor = document.createElement("a");
    expect(anchor.download).toBe("test file.docx");
  });

  it("should handle unquoted filename in Content-Disposition", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();
    headers.set("Content-Disposition", "filename=unquoted_file.docx");

    downloadBlob(blob, headers, "document.docx");

    const anchor = document.createElement("a");
    expect(anchor.download).toBe("unquoted_file.docx");
  });

  it("should set anchor element styles correctly", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    downloadBlob(blob, headers);

    const anchor = document.createElement("a");
    expect(anchor.style.display).toBe("none");
    expect(anchor.style.position).toBe("absolute");
    expect(anchor.style.left).toBe("-9999px");
    expect(anchor.style.top).toBe("-9999px");
    expect(anchor.style.visibility).toBe("hidden");
    expect(anchor.style.opacity).toBe("0");
  });

  it("should append and remove anchor element from DOM", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    downloadBlob(blob, headers);

    expect(mockAppendChild).toHaveBeenCalled();
    expect(mockRemoveChild).toHaveBeenCalled();
  });

  it("should restore scroll position if it changes during download", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    // Simulate scroll position change
    Object.defineProperty(window, "scrollY", {
      writable: true,
      configurable: true,
      value: 200,
    });

    downloadBlob(blob, headers);

    expect(global.requestAnimationFrame).toHaveBeenCalled();
    expect(window.scrollTo).toHaveBeenCalledWith(0, 100);
  });
});
