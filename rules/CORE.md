# CDDA Mod開発 コアルール

## 開発の進め方
1. 実装前に必ず設計書（templates/design_template.md）を作成する
2. external/cdda/data/json/ を参照してIDやフラグの正確な綴りを確認する
3. 実装後は必ずJSONの構文チェックを行う（scripts/validate.sh）
4. validate.sh通過後、modをexternal/cdda/mods/に配置しCDDA組み込みチェックを行う（scripts/check_mods.sh）。詳細はrules/verification.md参照

## 命名規則
- IDは必ず `mod_prefix_` で始める（例: `mymod_iron_rod`）
- IDに使える文字: 英小文字・数字・アンダースコアのみ
- IDに `#` 文字は使用不可

## 単位（0.H以降）
- 重量: `"500 g"` 形式（旧modが数値のみの場合は変換が必要）
- 容量: `"1500 ml"` 形式（旧modが数値のみの場合は変換が必要）
- 価格: `"200 USD"` 形式

## modinfo.json
- `type`: 必ず `"MOD_INFO"`
- `id`: 必須。他modと重複しない一意のID
- `name`: 必須
- `dependencies`: `[ "dda" ]` を最低限記載する

## copy-from の使い方
- 使用前に external/cdda/data/json/ で親IDの存在を確認する
- abstract アイテムを copy-from する場合、`abstract` フィールドは引き継がれない

## バージョン差分（0.G → 0.H）
- volume/weight の単位が数値から文字列形式に変更
  - 旧: `"volume": 3` → 新: `"volume": "750 ml"`
  - 旧: `"weight": 500` → 新: `"weight": "500 g"`
- その他の差分は version_diff.md を参照

## recipe の必須フィールド（0.I RC）
- `activity_level` が必須。省略するとゲーム起動時にエラー
- 値は `external/cdda/data/json/recipes/` の同カテゴリファイルを参照して選ぶ
- 武器・工具の製作は通常 `"BRISK_EXERCISE"`

## name フィールド形式（0.I RC）
- `ITEM`/`MONSTER`/`SPELL` → `{"str_sp": "名称"}` が必須（単純文字列は不可）
  - **ただし `TOOL` subtype のみ例外:** TOOL アイテムは `{"str": "名称"}` を使用（`str_sp` ではない）
  - **COMESTIBLE/FOOD/DRINK は `str_sp`:** 食品・飲料系も `ITEM` 型だが、`str_sp` が必須
- `overmap_terrain`/`mutation`/`profession` → 単純文字列が必須（`str_sp` は不可）

## よくあるエラー
- `unknown type` → typeフィールドのスペルミス
- `copy-from target not found` → 依存modの読み込み順か、IDのスペルミス
- `missing required field` / `missing mandatory member` → common_errors.md を参照
- JSON構文エラー → 末尾カンマ、括弧の対応を確認