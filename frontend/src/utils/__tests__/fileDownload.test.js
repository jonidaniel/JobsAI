import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { downloadBlob } from "../fileDownload";

describe("downloadBlob", () => {
  let mockCreateObjectURL;
  let mockRevokeObjectURL;
  let mockAppendChild;
  let mockRemoveChild;
  let mockClick;
  let mockAnchor;

  beforeEach(() => {
    // Mock URL.createObjectURL and revokeObjectURL
    mockCreateObjectURL = vi.fn(() => "blob:mock-url");
    mockRevokeObjectURL = vi.fn();
    window.URL.createObjectURL = mockCreateObjectURL;
    window.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock DOM methods
    mockClick = vi.fn();
    mockAppendChild = vi.fn();
    mockRemoveChild = vi.fn();

    // Create mock anchor element (create fresh for each test)
    mockAnchor = {
      href: "",
      download: "",
      style: {
        display: "",
        position: "",
        left: "",
        top: "",
        visibility: "",
        opacity: "",
      },
      setAttribute: vi.fn(),
      click: mockClick,
      parentNode: document.body,
      remove: undefined, // Will be set if available
    };

    // Mock document.createElement to return our mock anchor
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
    window.requestAnimationFrame = vi.fn((cb) => {
      cb();
      return 1;
    });
    window.scrollTo = vi.fn();
  });

  afterEach(() => {
    // Reset mock anchor properties
    mockAnchor.download = "";
    mockAnchor.href = "";
    mockAnchor.style.display = "";
    mockAnchor.style.position = "";
    mockAnchor.style.left = "";
    mockAnchor.style.top = "";
    mockAnchor.style.visibility = "";
    mockAnchor.style.opacity = "";
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
    expect(mockAnchor.download).toBe("document.docx");
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

    expect(mockAnchor.download).toBe("test_file.docx");
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

    expect(mockAnchor.download).toBe("test file.docx");
  });

  it("should handle unquoted filename in Content-Disposition", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();
    headers.set("Content-Disposition", "filename=unquoted_file.docx");

    downloadBlob(blob, headers, "document.docx");

    expect(mockAnchor.download).toBe("unquoted_file.docx");
  });

  it("should set anchor element styles correctly", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    downloadBlob(blob, headers);

    expect(mockAnchor.style.display).toBe("none");
    expect(mockAnchor.style.position).toBe("absolute");
    expect(mockAnchor.style.left).toBe("-9999px");
    expect(mockAnchor.style.top).toBe("-9999px");
    expect(mockAnchor.style.visibility).toBe("hidden");
    expect(mockAnchor.style.opacity).toBe("0");
  });

  it("should append and remove anchor element from DOM", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    downloadBlob(blob, headers);

    expect(mockAppendChild).toHaveBeenCalledWith(mockAnchor);
    // Check that remove was attempted (either remove() or removeChild)
    // Since we're using removeChild fallback in jsdom, check for that
    expect(mockRemoveChild).toHaveBeenCalledWith(mockAnchor);
  });

  it("should restore scroll position if it changes during download", () => {
    const blob = new Blob(["test content"], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const headers = new Headers();

    // Set initial scroll position (saved before click)
    Object.defineProperty(window, "scrollY", {
      writable: true,
      configurable: true,
      value: 100,
    });

    downloadBlob(blob, headers);

    // After download, simulate scroll change
    Object.defineProperty(window, "scrollY", {
      writable: true,
      configurable: true,
      value: 200,
    });

    // requestAnimationFrame callback should restore scroll
    expect(window.requestAnimationFrame).toHaveBeenCalled();
    // The callback will check scrollY (now 200) vs scrollBeforeClick (100) and restore
    const rafCallback = window.requestAnimationFrame.mock.calls[0][0];
    rafCallback();
    expect(window.scrollTo).toHaveBeenCalledWith(0, 100);
  });
});
