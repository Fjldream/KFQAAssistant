import { describe, expect, it } from "vitest";
import { normalizeApiBaseUrl, resolveImageUrl } from "./client";

describe("normalizeApiBaseUrl", () => {
  it("removes trailing slashes", () => {
    expect(normalizeApiBaseUrl("http://127.0.0.1:8000///")).toBe("http://127.0.0.1:8000");
  });
});

describe("resolveImageUrl", () => {
  it("converts manual relative paths to backend static URLs", () => {
    expect(resolveImageUrl("http://127.0.0.1:8000/", "/html/about/1.png")).toBe(
      "http://127.0.0.1:8000/manuals/html/about/1.png",
    );
  });

  it("keeps remote image URLs unchanged", () => {
    expect(resolveImageUrl("http://127.0.0.1:8000", "https://example.com/a.png")).toBe(
      "https://example.com/a.png",
    );
  });
});
