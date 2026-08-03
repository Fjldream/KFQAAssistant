import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { SourceSnippet } from "../api/types";
import MaterialReader from "./MaterialReader.vue";

describe("MaterialReader", () => {
  it("renders the selected material as a page-wide manual reader", async () => {
    const source: SourceSnippet = {
      title: "工程开发-Windows",
      source_path: "html/数采管理/工程开发-Windows/index.html",
      snippet: "点击新建工程按钮，可以新建数采工程，并填写名称、平台和描述。",
      evidence_ids: ["资料 1"],
      images: ["html/数采管理/工程开发-Windows/1.png"],
      score: 0.82,
    };
    const wrapper = mount(MaterialReader, {
      props: {
        source,
        apiBaseUrl: "http://127.0.0.1:8000/",
      },
    });

    expect(wrapper.get(".ki-material-dialog").classes()).toContain("ki-material-dialog--page");
    expect(wrapper.text()).toContain("工程开发-Windows");
    expect(wrapper.text()).toContain("点击新建工程按钮");
    expect(wrapper.get(".ki-image-thumb img").attributes("src")).toBe(
      "http://127.0.0.1:8000/manuals/html/数采管理/工程开发-Windows/1.png",
    );

    await wrapper.get(".ki-image-thumb").trigger("click");

    expect(wrapper.emitted("previewImage")?.[0]).toEqual([
      "http://127.0.0.1:8000/manuals/html/数采管理/工程开发-Windows/1.png",
    ]);
  });
});
