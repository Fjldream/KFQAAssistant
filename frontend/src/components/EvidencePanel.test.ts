import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { SourceSnippet } from "../api/types";
import EvidencePanel from "./EvidencePanel.vue";

describe("EvidencePanel", () => {
  it("emits openMaterial and keeps the reader outside the side panel", async () => {
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

    await wrapper.get(".ki-source-item").trigger("click");

    expect(wrapper.emitted("openMaterial")?.[0]).toEqual([source]);
    expect(wrapper.find(".ki-material-dialog").exists()).toBe(false);
  });
});
