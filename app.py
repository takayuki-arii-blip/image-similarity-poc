"""Streamlit UI for comparing two product images with OpenAI vision."""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Literal

import streamlit as st
from openai import OpenAI
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field


DISCLAIMER = "本評価は商品企画上の参考情報であり、法的な権利侵害の有無を判定するものではありません。"
MAX_FILE_SIZE = 10 * 1024 * 1024
ASPECT_NAMES = (
    "全体シルエット",
    "襟・首回り",
    "袖",
    "ポケット",
    "切替・構造線",
    "柄・グラフィック",
    "配色",
    "装飾・ディテール",
)


class AspectResult(BaseModel):
    name: Literal[
        "全体シルエット",
        "襟・首回り",
        "袖",
        "ポケット",
        "切替・構造線",
        "柄・グラフィック",
        "配色",
        "装飾・ディテール",
    ]
    score: int = Field(ge=0, le=100)
    comment: str


class ComparisonResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    similarity_level: Literal["高", "中", "低"]
    overall_comment: str
    aspects: list[AspectResult] = Field(min_length=8, max_length=8)
    main_similarities: list[str]
    main_differences: list[str]


def get_api_key() -> str | None:
    """Read the API key without embedding it in source code."""
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    except (FileNotFoundError, KeyError):
        return os.getenv("OPENAI_API_KEY")


def prepare_image(uploaded_file) -> tuple[bytes, str]:
    """Validate an uploaded image and return its transient bytes and MIME type."""
    data = uploaded_file.getvalue()
    if not data:
        raise ValueError("画像ファイルが空です。")
    if len(data) > MAX_FILE_SIZE:
        raise ValueError("画像は1枚あたり10MB以下にしてください。")
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
            image_format = image.format
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("有効な画像ファイルを選択してください。") from exc

    mime_types = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    if image_format not in mime_types:
        raise ValueError("対応形式はJPG、PNG、WEBPです。")
    return data, mime_types[image_format]


def image_data_url(data: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def compare_images(client: OpenAI, image_a: tuple[bytes, str], image_b: tuple[bytes, str]) -> ComparisonResult:
    """Request a structured, design-focused comparison from OpenAI."""
    prompt = f"""あなたは商品デザインの画像比較アシスタントです。2枚の商品画像の視覚的な類似性を日本語で評価してください。
法的な権利侵害、模倣、真正性は判定せず、商品企画の参考となる観察事実だけを述べてください。
総合スコアは0〜100。類似性レベルは、高=70〜100、中=40〜69、低=0〜39としてください。
次の8項目をこの順序で、漏れなく各1回評価してください: {', '.join(ASPECT_NAMES)}。
画像から確認できない項目は推測せず、その旨をコメントに記載してください。
類似点と相違点は簡潔で具体的な箇条書きにしてください。"""
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_text", "text": "画像A"},
                    {"type": "input_image", "image_url": image_data_url(*image_a), "detail": "high"},
                    {"type": "input_text", "text": "画像B"},
                    {"type": "input_image", "image_url": image_data_url(*image_b), "detail": "high"},
                ],
            }
        ],
        text_format=ComparisonResult,
    )
    if response.output_parsed is None:
        raise ValueError("AIから比較結果を取得できませんでした。")
    result = response.output_parsed
    if [aspect.name for aspect in result.aspects] != list(ASPECT_NAMES):
        by_name = {aspect.name: aspect for aspect in result.aspects}
        if set(by_name) != set(ASPECT_NAMES):
            raise ValueError("AIの回答に必要な評価項目が含まれていません。")
        result.aspects = [by_name[name] for name in ASPECT_NAMES]
    return result


def render_result(result: ComparisonResult) -> None:
    st.subheader("比較結果")
    score_col, level_col = st.columns(2)
    score_col.metric("総合類似度", f"{result.overall_score}%")
    level_col.metric("類似性レベル", result.similarity_level)
    st.progress(result.overall_score / 100)
    st.markdown(f"**総合コメント**  \n{result.overall_comment}")

    st.markdown("#### 項目別評価")
    for aspect in result.aspects:
        with st.container(border=True):
            left, right = st.columns([3, 1])
            left.markdown(f"**{aspect.name}**")
            right.markdown(f"**{aspect.score}%**")
            st.progress(aspect.score / 100)
            st.write(aspect.comment)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 主な類似点")
        for item in result.main_similarities:
            st.markdown(f"- {item}")
    with col_b:
        st.markdown("#### 主な相違点")
        for item in result.main_differences:
            st.markdown(f"- {item}")


def main() -> None:
    st.set_page_config(page_title="商品画像 類似性チェック", page_icon="🔍", layout="wide")
    st.title("商品画像 類似性チェック")
    st.caption("2枚の商品画像をAIがデザイン要素ごとに比較します。")
    st.info(f"⚠️ {DISCLAIMER}")

    upload_a, upload_b = st.columns(2)
    with upload_a:
        file_a = st.file_uploader("画像Aをアップロード", type=["jpg", "jpeg", "png", "webp"], key="a")
        if file_a:
            st.image(file_a, caption="画像A", use_container_width=True)
    with upload_b:
        file_b = st.file_uploader("画像Bをアップロード", type=["jpg", "jpeg", "png", "webp"], key="b")
        if file_b:
            st.image(file_b, caption="画像B", use_container_width=True)

    if st.button("AIで比較する", type="primary", use_container_width=True, disabled=not (file_a and file_b)):
        api_key = get_api_key()
        if not api_key:
            st.error("OPENAI_API_KEYが設定されていません。Streamlit Secretsまたは環境変数に設定してください。")
            return
        try:
            image_a = prepare_image(file_a)
            image_b = prepare_image(file_b)
            with st.spinner("AIが画像を比較しています…"):
                result = compare_images(OpenAI(api_key=api_key), image_a, image_b)
            render_result(result)
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error("比較中にエラーが発生しました。APIキー、通信状況、画像形式を確認してもう一度お試しください。")
            st.caption(f"エラー種別: {type(exc).__name__}")

    st.divider()
    st.caption("アップロード画像は比較リクエストの処理にのみ使用し、このアプリでは永続保存しません。")


if __name__ == "__main__":
    main()
