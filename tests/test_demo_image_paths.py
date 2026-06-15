from pathlib import Path

from demo.image_paths import resolve_demo_image_path


def test_resolve_demo_image_path_uses_data_dir_for_manual_relative_paths(tmp_path: Path):
    data_dir = tmp_path / "help"
    image_path = data_dir / "html" / "about" / "1.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"png")

    resolved = resolve_demo_image_path("html/about/1.png", data_dir=data_dir)

    assert resolved == str(image_path)


def test_resolve_demo_image_path_returns_none_for_missing_local_file(tmp_path: Path):
    resolved = resolve_demo_image_path("html/about/missing.png", data_dir=tmp_path / "help")

    assert resolved is None
