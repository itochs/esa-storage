# esa-exporter

`esa-exporter` は、esa API から記事を取得し、Markdown と画像としてローカル保存する CLI です。

## 前提

- Python 3.12+
- `uv`
- esa のアクセストークン

このリポジトリは workspace 構成です。ルートで `uv sync` を実行すると利用できます。

## トークン設定

トークンは次の優先順で読み込みます。

1. 環境変数 `ESA_ACCESS_TOKEN`
2. 環境変数 `ESA_TOKEN`
3. 環境変数 `ESA_API_TOKEN`
4. `--env-file` で指定したファイル（デフォルト `.env`）

`.env` は以下どちらの形式でも読み込めます。

```dotenv
ESA_ACCESS_TOKEN=xxxxxxxx
```

```dotenv
xxxxxxxx
```

## クイックスタート

```bash
uv sync
uv run esa-exporter pull --team <team-name> --user <screen-name>
```

## コマンド

### `fetch`

esa API から記事一覧を取得し、レスポンス JSON を保存します。

```bash
uv run esa-exporter fetch --team <team-name> --user <screen-name>
```

主なオプション:

- `--team`
- `--user`
- `--responses-dir` (default: `responce`)
- `--env-file` (default: `.env`)
- `--no-wip` 下書き（WIP）投稿を除外

差分取得:

- `<responses-dir>/.last_sync_date` がある場合、その日付を `updated:>=YYYY-MM-DD` クエリに使います。
- 取得後、最も新しい `updated_at` の日付で `.last_sync_date` を更新します。

### `save`

`fetch` で保存された JSON から Markdown と画像を出力します。

```bash
uv run esa-exporter save
```

主なオプション:

- `--posts-dir` (default: `posts`)
- `--images-dir` (default: `images`)
- `--responses-dir` (default: `responce`)
- `--env-file` (default: `.env`)

### `pull`

`fetch` と `save` を連続で実行します。

```bash
uv run esa-exporter pull --team <team-name> --user <screen-name>
```

主なオプション:

- `--team`
- `--user`
- `--responses-dir` (default: `responce`)
- `--posts-dir` (default: `posts`)
- `--images-dir` (default: `images`)
- `--env-file` (default: `.env`)
- `--no-wip` 下書き（WIP）投稿を除外

実行時の挙動:

- 初回（`<responses-dir>/.last_sync_date` がない）: `fetch` は更新日フィルタなしで取得し、続けて `save` で Markdown/画像を出力します。
- 2回目以降（`<responses-dir>/.last_sync_date` がある）: `fetch` は `updated:>=YYYY-MM-DD` の条件で差分取得し、続けて `save` で更新分のみ反映します。

出力仕様:

- 記事: `<posts-dir>/<category>/<number>_<sanitized-title>.md`  
  カテゴリが空の場合は `<posts-dir>/<number>_<sanitized-title>.md`
- 画像: `<images-dir>/...`
- Markdown/HTML の画像 URL はローカル相対パスに置換
- 既存 Markdown の `number` と `updated_at` が一致する記事はスキップ

## 実行例

```bash
# JSON 取得から Markdown / 画像保存まで
uv run esa-exporter pull --team my-team --user my-user
```

```bash
# 出力先をカスタマイズ
uv run esa-exporter pull \
  --team my-team \
  --user my-user \
  --posts-dir ./backup/posts \
  --images-dir ./backup/images \
  --responses-dir ./backup/responce
```

## 補足

- レスポンス保存ディレクトリ名は実装に合わせて `responce`（スペルそのまま）です。
- API / 画像ダウンロードの負荷制御として、内部で待機時間（sleep）を入れています。
