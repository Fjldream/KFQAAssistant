from langchain_community.embeddings import HuggingFaceEmbeddings


# 创建本地 HuggingFace embedding 模型，用于把文本和问题转成向量。
def create_embeddings(model_name: str):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={"normalize_embeddings": True},
    )
