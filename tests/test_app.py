from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

from app import ASPECT_NAMES, ComparisonResult, image_data_url, prepare_image


def upload(image_format="PNG", size=(2, 2)):
    buffer = BytesIO()
    Image.new("RGB", size, "blue").save(buffer, format=image_format)
    return SimpleNamespace(getvalue=lambda: buffer.getvalue())


def test_prepare_image_accepts_png():
    data, mime = prepare_image(upload())
    assert data.startswith(b"\x89PNG")
    assert mime == "image/png"


def test_prepare_image_rejects_invalid_data():
    with pytest.raises(ValueError, match="有効な画像"):
        prepare_image(SimpleNamespace(getvalue=lambda: b"not an image"))


def test_data_url():
    assert image_data_url(b"abc", "image/png") == "data:image/png;base64,YWJj"


def test_result_schema_enforces_score_range():
    aspects = [{"name": name, "score": 50, "comment": "コメント"} for name in ASPECT_NAMES]
    result = ComparisonResult(
        overall_score=50,
        similarity_level="中",
        overall_comment="コメント",
        aspects=aspects,
        main_similarities=["類似点"],
        main_differences=["相違点"],
    )
    assert len(result.aspects) == 8

    with pytest.raises(ValueError):
        ComparisonResult(
            overall_score=101,
            similarity_level="高",
            overall_comment="コメント",
            aspects=aspects,
            main_similarities=[],
            main_differences=[],
        )
