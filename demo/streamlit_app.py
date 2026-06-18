import html
import os
from typing import Any

import requests
import streamlit as st

try:
    from demo.ui_helpers import (
        DEMO_EXAMPLE_QUESTIONS,
        evidence_label,
        resolved_source_images,
        score_label,
        snippet_preview,
    )
except ModuleNotFoundError:
    from ui_helpers import DEMO_EXAMPLE_QUESTIONS, evidence_label, resolved_source_images, score_label
    from ui_helpers import snippet_preview


DEFAULT_API_URL = os.getenv("KF_RAG_API_URL", "http://127.0.0.1:8000/api/chat")

st.set_page_config(page_title="KF RAG 问答助手", layout="wide")
st.markdown(
    """
    <style>
    .source-snippet {
        color: #4b5563;
        font-size: 0.94rem;
        line-height: 1.55;
        padding: 0.25rem 0 0.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# 初始化 Streamlit 页面状态，保存问题、回答和当前 API 地址。
def init_state() -> None:
    st.session_state.setdefault("question", "")
    st.session_state.setdefault("api_url", DEFAULT_API_URL)
    st.session_state.setdefault("last_response", None)


# 调用后端 RAG 接口，并把 HTTP 错误转换成页面可展示的异常信息。
def ask_api(api_url: str, question: str) -> dict[str, Any]:
    response = requests.post(api_url, json={"question": question}, timeout=120)
    response.raise_for_status()
    return response.json()


# 渲染一个来源下的图片，图片按来源折叠展示，避免页面被长图列表撑开。
def render_source_images(source: dict[str, Any]) -> None:
    images = resolved_source_images(source)
    if not images:
        return

    available_images = [image for image in images if image["exists"]]
    missing_images = [image for image in images if not image["exists"]]
    with st.expander(f"图片 {len(available_images)} 张", expanded=False):
        if available_images:
            columns = st.columns(min(3, len(available_images)))
            for index, image in enumerate(available_images):
                with columns[index % len(columns)]:
                    st.image(image["resolved_path"], caption=image["path"], use_container_width=True)
        for image in missing_images:
            st.caption(f"图片文件不存在：{image['path']}")


# 渲染单条来源卡片，包括资料编号、相似度、路径、片段和图片。
def render_source(source: dict[str, Any], index: int) -> None:
    with st.container(border=True):
        left, right = st.columns([0.7, 0.3])
        with left:
            st.markdown(f"**{evidence_label(source)} · {source.get('title', f'来源 {index}')}**")
        with right:
            st.markdown(f"`{score_label(source)}`")
        st.code(source.get("source_path", ""), language="text")
        st.markdown(
            f'<div class="source-snippet">{html.escape(snippet_preview(source))}</div>',
            unsafe_allow_html=True,
        )
        render_source_images(source)


# 渲染问答结果区域，回答在上，来源和图片在下。
def render_response(data: dict[str, Any]) -> None:
    st.subheader("回答")
    st.markdown(data.get("answer", ""))

    sources = data.get("sources", [])
    st.subheader(f"来源 {len(sources)}")
    if not sources:
        st.info("没有返回来源。")
        return

    for index, source in enumerate(sources, start=1):
        render_source(source, index)


# 渲染左侧提问区，包括 API 地址、示例问题和问题输入框。
def render_question_panel() -> tuple[str, bool]:
    st.sidebar.title("KF RAG")
    st.sidebar.text_input("API 地址", key="api_url")
    st.sidebar.markdown("**示例问题**")
    for question in DEMO_EXAMPLE_QUESTIONS:
        if st.sidebar.button(question, use_container_width=True):
            st.session_state["question"] = question

    with st.sidebar.form("question_form"):
        question = st.text_area("问题", key="question", height=140)
        submitted = st.form_submit_button("提问", use_container_width=True)
    return question.strip(), submitted


init_state()
st.title("KF RAG 问答助手 Demo")

question, submitted = render_question_panel()

if submitted:
    if not question:
        st.warning("请输入问题。")
    else:
        with st.spinner("正在检索手册并生成回答..."):
            try:
                st.session_state["last_response"] = ask_api(st.session_state["api_url"], question)
            except requests.RequestException as exc:
                st.session_state["last_response"] = None
                st.error(f"接口调用失败：{exc}")

if st.session_state["last_response"]:
    render_response(st.session_state["last_response"])
else:
    st.info("等待提问。")
