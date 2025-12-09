# esa

esaにある自分の記事をまとめる

## 使い方

1. esa のアクセストークンを `.env` に保存します。
   - 推奨: `ESA_ACCESS_TOKEN=xxxxxxxx` という形式で書く。
   - `.env` にトークンだけ 1 行で書いてある場合でも読み取ります。
2. 依存インストール（requests を使います）。`python -m pip install requests`
3. 使い方（ライブラリ + CLI）
   - 取得: raw JSON を `responce/` に保存

     ```bash
     python -m esa_exporter.cli fetch --team vdslab --user ito_hal
     # or after installing: esa-exporter fetch --team vdslab --user ito_hal
     # uv を使う場合: uv run -m esa_exporter.cli fetch --team vdslab --user ito_hal
     ```

     - 下書き（wip）も含めます。除外したいときは `--no-wip`。
     - `responce/.last_sync_date` があれば `updated:>=` クエリで差分取得し、最新の `updated_at` 日付を更新します。
   - 保存: 未保存の記事だけ Markdown と画像を出力

     ```bash
     python -m esa_exporter.cli save
     # or: esa-exporter save
     # uv を使う場合: uv run -m esa_exporter.cli save
     ```

     - Markdown は `posts/<カテゴリ>/<number>_<タイトル>.md`、画像は `images/` に保存し、Markdown 内リンクをローカル参照に書き換えます。
     - すでにローカルに同じ `number` かつ同じ `updated_at` がある記事はスキップ（差分のみ保存）。
   - 保存先を変えたい場合は `--posts-dir` / `--images-dir` / `--responses-dir` を指定してください。

構成

- `esa_exporter/core.py`: 共有ロジック（API コール、保存処理など）。
- `esa_exporter/cli/`: CLI 実装（`fetch` / `save` サブコマンド）。`python -m esa_exporter.cli ...` で呼び出し。
