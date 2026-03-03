# esa-storage

esa の記事をローカルにエクスポートするためのワークスペースです。  
日常的な利用は `pull` コマンド 1 つで完結します。

## 前提

このプロジェクトでは `uv` を使用します。未インストールの場合は、公式ドキュメントを参照してセットアップしてください。

<https://docs.astral.sh/uv/getting-started/installation/>

## クイックスタート

1. `.env` を作成し、esa のアクセストークンを設定します。  
   トークンの取得方法は、esa API v1 ドキュメントを参照してください。
   <https://docs.esa.io/posts/102#認証と認可>

   ```dotenv
   ESA_ACCESS_TOKEN=xxxxxxxx
   ```

2. 依存関係をインストールします。

   ```bash
   uv sync
   ```

3. 記事を取得してローカルへ保存します。

   ```bash
   uv run esa-exporter pull --team <team-name> --user <screen-name>
   ```

## よく使うコマンド

基本実行:

```bash
uv run esa-exporter pull --team <team-name> --user <screen-name>
```

下書き（WIP）を除外:

```bash
uv run esa-exporter pull --team <team-name> --user <screen-name> --no-wip
```

出力先を変更:

```bash
uv run esa-exporter pull \
  --team <team-name> \
  --user <screen-name> \
  --posts-dir ./my_posts \
  --images-dir ./my_images \
  --responses-dir ./my_responses
```

## 補足

- 詳細仕様（`fetch` / `save` の個別実行、差分取得の挙動、全オプション）は [`esa_exporter/README.md`](esa_exporter/README.md) を参照してください。
