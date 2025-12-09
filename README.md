# esa
esaにある自分の記事をまとめる

## 使い方
1. esa のアクセストークンを `.env` に保存します。
   - 推奨: `ESA_ACCESS_TOKEN=xxxxxxxx` という形式で書く。
   - `.env` にトークンだけ 1 行で書いてある場合でも読み取ります。
2. 依存インストール（requests を使います）。`python -m pip install requests`
3. エクスポート実行:
   ```
   python sync_esa.py --team vdslab --user ito_hal
   ```
   - デフォルトで `posts/<カテゴリ>/<タイトル>.md` に本文を保存し、画像は `images/` にダウンロードして Markdown 内の URL を差し替えます。
   - 下書き（wip）も含めます。除外したいときは `--no-wip`。
   - 出力先を変えたい場合は `--posts-dir` や `--images-dir` を指定してください。
