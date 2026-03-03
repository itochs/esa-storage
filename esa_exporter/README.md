# esa-exporter

`esa-exporter` は、esa API から記事を取得し、Markdown と画像としてローカル保存する CLI です。

## 前提

- Python 3.12+
- `uv`
- esa のアクセストークン

このリポジトリでは workspace 構成のため、ルートで `uv sync` すると利用できます。

## トークン設定

次の優先順でトークンを読み込みます。

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

## 最小手順

```bash
uv sync
uv run esa-exporter fetch --team <team-name> --user <screen-name>
uv run esa-exporter save
```

## コマンド

### `fetch`

esa API から記事一覧を取得し、raw JSON を保存します。

```bash
uv run esa-exporter fetch --team <team-name> --user <screen-name>
```

主なオプション:

- `--team`
- `--user`
- `--responses-dir` (default: `responce`)
- `--env-file` (default: `.env`)
- `--no-wip` 下書き投稿を除外

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

出力仕様:

- 記事: `<posts-dir>/<category>/<number>_<sanitized-title>.md`  
  カテゴリが空の場合は `<posts-dir>/<number>_<sanitized-title>.md`
- 画像: `<images-dir>/...`
- Markdown/HTML の画像 URL はローカル相対パスに置換
- 既存 Markdown の `number` と `updated_at` が一致する記事はスキップ

## 実行例

```bash
# 1) JSON取得（wip込み）
uv run esa-exporter fetch --team my-team --user my-user

# 2) Markdownと画像を書き出し
uv run esa-exporter save
```

```bash
# 出力先をカスタマイズ
uv run esa-exporter save \
  --posts-dir ./backup/posts \
  --images-dir ./backup/images \
  --responses-dir ./backup/responce
```

## 補足

- レスポンス保存ディレクトリ名は実装に合わせて `responce`（スペルそのまま）です。
- API / 画像ダウンロードの負荷制御として、内部で待機時間（sleep）を入れています。
