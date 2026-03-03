# esa

esa の記事をローカルにエクスポートするためのワークスペースです。

## 前提

このプロジェクトでは `uv` を使用します。  
未インストールの場合は、以下の公式ドキュメントを参照してセットアップしてください。

<https://docs.astral.sh/uv/getting-started/installation/>

## クイックスタート

1. `.env` を作成してトークンを設定します。

   ```dotenv
   ESA_ACCESS_TOKEN=xxxxxxxx
   ```

2. 依存関係をインストールします。

   ```bash
   uv sync
   ```

3. 投稿データを取得して保存します。

   ```bash
   uv run esa-exporter fetch --team <team-name> --user <user-name>
   uv run esa-exporter save
   ```

## よく使う実行パターン

初回: 取得して保存

```bash
uv run esa-exporter fetch --team <team-name> --user <user-name>
uv run esa-exporter save
```

2回目以降: 差分取得して保存（`.last_sync_date` を利用）

```bash
uv run esa-exporter fetch --team <team-name> --user <user-name>
uv run esa-exporter save
```

下書き（wip）を除外して取得

```bash
uv run esa-exporter fetch --team <team-name> --user <user-name> --no-wip
```

出力先を変更

```bash
uv run esa-exporter save \
  --posts-dir ./my_posts \
  --images-dir ./my_images \
  --responses-dir ./my_responses
```

## 補足

- `fetch` は `responce/` に `esa_page_*.json` を保存します。
- `responce/.last_sync_date` がある場合、`updated:>=<date>` で差分取得します。
- `save` は `posts/<category>/<number>_<title>.md` と `images/` を出力します。
- ローカルに同じ `number` かつ同じ `updated_at` の記事はスキップします。
- パッケージ詳細と全オプションは [`esa_exporter/README.md`](esa_exporter/README.md) を参照してください。
