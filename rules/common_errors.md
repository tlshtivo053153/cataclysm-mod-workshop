# よくあるエラーと解決策

## エラー一覧

### `unknown type: XXX`
- **原因:** `type` フィールドの値のスペルミス
- **種別:** rule
- **解決策:** `external/cdda/data/json/` で正しい type 名を検索して確認する
- **例:** `"type": "GENRIC"` → `"type": "GENERIC"`

### `can't find copy_from target 'XXX'`
- **原因:** `copy-from` で指定したIDが存在しない
- **種別:** rule
- **解決策:**
  1. `external/cdda/data/json/` でIDを grep して存在確認する
  2. 依存modが `dependencies` に記載されているか確認する
  3. IDのスペルミスを確認する

### `JSON parse error` / `unexpected token`
- **原因:** JSONの構文エラー
- **種別:** rule
- **解決策:** `scripts/validate.sh` を実行してエラー行を確認する。末尾カンマ、括弧の対応を確認する

### `missing required field: XXX`
- **原因:** 必須フィールドが欠けている
- **種別:** rule
- **解決策:** `external/cdda/doc/JSON/JSON_INFO.md` で該当 type の必須フィールドを確認する

### volume/weight の値が不正
- **原因:** 旧バージョン形式（数値）のまま移植した
- **種別:** rule
- **解決策:** `version_diff.md` の単位変換表を参照して文字列形式に変換する

### `missing mandatory member "activity_level"`
- **原因:** recipe に `activity_level` フィールドが欠けている（0.I RC で必須化）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** recipe オブジェクトに `"activity_level"` を追加する
- **有効な値:**
  - `"LIGHT_EXERCISE"` — 軽作業（縫製・料理など）
  - `"BRISK_EXERCISE"` — 中程度の作業（一般的な工作・武器製作）
  - `"MODERATE_EXERCISE"` — やや重い作業
  - `"ACTIVE_EXERCISE"` — 重労働（金属加工・鍛冶）
- **例:**
  ```json
  {
    "type": "recipe",
    "activity_level": "BRISK_EXERCISE",
    "result": "my_item",
    ...
  }
  ```
- **確認方法:** `external/cdda/data/json/recipes/` の同カテゴリのレシピを参照する

---
※ 新しいエラーが発生したらこのファイルに追記する