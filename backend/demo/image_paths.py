from pathlib import Path
from urllib.parse import urlparse


# 判断图片路径是否已经是浏览器可直接访问的 URL。
def _is_url(image: str) -> bool:
    parsed = urlparse(image)
    return parsed.scheme in {"http", "https"}


# 把接口返回的手册图片相对路径解析为 Streamlit 可读取的本地文件路径。
def resolve_demo_image_path(image: str, data_dir: Path = Path("data/help")) -> str | None:
    if _is_url(image):
        return image

    image_path = Path(image)
    if image_path.is_absolute():
        return str(image_path) if image_path.exists() else None

    manual_image_path = data_dir / image_path
    if manual_image_path.exists():
        return str(manual_image_path)

    return None
