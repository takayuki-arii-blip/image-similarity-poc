# 商品画像 類似性チェック

商品企画担当者が2枚の商品画像をアップロードし、OpenAIの画像認識モデルでデザイン上の類似点・相違点を確認するためのStreamlit PoCです。法的な権利侵害を判定する用途ではありません。

## 主な機能

- JPG / PNG / WEBP画像2枚の横並びプレビュー（各10MBまで）
- 総合類似度、類似性レベル、総合コメントの表示
- 8つのデザイン要素ごとの類似度とコメント
- 主な類似点・相違点の表示
- PydanticによるAI回答形式の検証
- 画像をディスクやデータベースへ永続保存しない処理

## ローカル実行

Python 3.11以上を推奨します。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

APIキーは、環境変数またはStreamlit Secretsのいずれかで設定します。

### 環境変数を使う場合

```bash
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```

### Streamlit Secretsを使う場合

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# .streamlit/secrets.toml の値を実際のAPIキーに変更
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開きます。`.streamlit/secrets.toml` はGit管理対象外です。

## Streamlit Community Cloudへデプロイ

1. このリポジトリをGitHubへpushします。
2. [Streamlit Community Cloud](https://share.streamlit.io/) にサインインし、**Create app**を選択します。
3. リポジトリ、ブランチ、エントリーポイント `app.py` を指定します。
4. **Advanced settings → Secrets** に次を登録します。

   ```toml
   OPENAI_API_KEY = "sk-..."
   ```

5. **Deploy**を押します。依存パッケージは`requirements.txt`から自動インストールされます。

API利用料は設定したOpenAIアカウントに発生します。公開アプリでは利用者制限やOpenAI側の利用上限も設定してください。

## テスト

```bash
pip install pytest
pytest -q
```

実際のAPI比較には有効な`OPENAI_API_KEY`が必要です。単体テストはAPIを呼び出しません。

## セキュリティとデータの取り扱い

- APIキーをコードへ直接記載しないでください。
- アップロード画像はメモリ上で処理し、このアプリ自体は永続保存しません。
- 比較時には画像データがOpenAI APIへ送信されます。機密画像を扱う場合は、組織のポリシーおよびOpenAIのデータ利用条件を確認してください。
- 本評価は商品企画上の参考情報であり、法的な権利侵害の有無を判定するものではありません。
