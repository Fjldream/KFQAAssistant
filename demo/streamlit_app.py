import os

import requests
import streamlit as st


API_URL = os.getenv("KF_RAG_API_URL", "http://127.0.0.1:8000/api/chat")

st.set_page_config(page_title="KF RAG 问答助手", layout="wide")
st.title("KF RAG 问答助手 Demo")

question = st.text_input("请输入 KF 产品使用问题")

if st.button("提问") and question.strip():
    response = requests.post(API_URL, json={"question": question.strip()}, timeout=120)
    response.raise_for_status()
    data = response.json()

    st.subheader("回答")
    st.write(data["answer"])

    st.subheader("来源")
    for source in data.get("sources", []):
        st.markdown(f"**{source['title']}**")
        st.code(source["source_path"])
        st.write(source["snippet"])
        for image in source.get("images", []):
            st.image(image, caption=image)
