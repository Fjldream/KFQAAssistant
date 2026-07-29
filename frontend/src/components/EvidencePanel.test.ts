import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { SourceSnippet } from "../api/types";
import EvidencePanel from "./EvidencePanel.vue";

describe("EvidencePanel", () => {
  it("emits resolved manual image URL when an image is clicked", async () => {
    const source: SourceSnippet = {
      title: "工程开发-Windows",
      source_path: "html/数采管理/工程开发-Windows/index.html",
      snippet: "点击新建工程按钮。",
      evidence_ids: ["资料 1"],
      images: ["html/数采管理/工程开发-Windows/1.png"],
      score: 0.82,
    };
    const wrapper = mount(EvidencePanel, {
      props: {
        sources: [source],
        selectedSource: source,
        apiBaseUrl: "http://127.0.0.1:8000/",
      },
    });

    await wrapper.get(".ki-image-thumb").trigger("click");

    expect(wrapper.emitted("previewImage")?.[0]).toEqual([
      "http://127.0.0.1:8000/manuals/html/数采管理/工程开发-Windows/1.png",
    ]);
  });
});
