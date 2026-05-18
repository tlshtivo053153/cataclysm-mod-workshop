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

### `Invalid or misplaced field name "traits" in JSON data` (field_type)
- **原因:** `field_type` の `immunity_data` で `traits` が廃止され `flags` に変更された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** `"immunity_data": { "traits": ["XXX"] }` → `"immunity_data": { "flags": ["XXX"] }`
- **例:** `"traits": ["WEB_WALKER"]` → `"flags": ["WEBWALK"]`

### `Invalid or misplaced field name "convection_temperature_mod" in JSON data` (field_type)
- **原因:** `convection_temperature_mod` が `effects` 配列内から `intensity_levels` レベルに移動した（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** `intensity_levels` 内の各レベルオブジェクトの `effects` 配列から `convection_temperature_mod` を外し、同じレベルオブジェクトの兄弟要素として配置する
- **例:**
  ```json
  // 旧（エラー）
  "intensity_levels": [{
    "effects": [{
      "effect_id": "downed",
      "convection_temperature_mod": -20,
      ...
    }]
  }]
  // 新（正しい）
  "intensity_levels": [{
    "convection_temperature_mod": -20,
    "effects": [{
      "effect_id": "downed",
      ...
    }]
  }]
  ```

### `Invalid or misplaced field name "dangerous" / "translucency" / "effects" in JSON data` (field_type)
- **原因:** `field_type` のルートレベルに配置していた `dangerous`, `translucency`, `effects` 等が `intensity_levels` 内に移動した（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** これらのフィールドを `intensity_levels` 配列内の各レベルオブジェクトに移動する

### `bound_reader failed to read value` / `price`
- **原因:** `price` / `price_postapoc` が数値形式から通貨文字列形式に変更された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** 数値を通貨文字列に変換する
  - `"price": 150` → `"price": "1 USD 50 cent"`
  - `"price": 1000` → `"price": "10 USD"`
  - `"price": 25` → `"price": "25 cent"`
  - `"price_postapoc": 0` → `"price_postapoc": "0 cent"`
- **一括変換スクリプト:** `scripts/convert_price.py`

### `unrecognized JSON object` / `type: "AMMO"`
- **原因:** `AMMO`, `GUN`, `ARMOR` 等の個別アイテムタイプが `ITEM` 型に統合された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** `"type": "AMMO"` → `"type": "ITEM", "subtypes": ["AMMO"]`
- **対象タイプ:** `AMMO`, `GUN`, `ARMOR`, `TOOL`, `TOOLMOD`, `TOOL_ARMOR`, `BOOK`, `COMESTIBLE`, `ENGINE`, `WHEEL`, `GUNMOD`, `MAGAZINE`, `GENERIC`, `BIONIC_ITEM` 等
- **例外:** `ammunition_type`（弾薬タイプ定義）はそのまま有効

### `Invalid enum string 'ARMOR_BALLISTIC'`
- **原因:** `enchant_vals::mod` から `ARMOR_*` 系の値が削除された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** `ARMOR_BALLISTIC`, `ARMOR_ACID`, `ARMOR_BASH`, `ARMOR_BIO`, `ARMOR_STAB`, `ARMOR_HEAT`, `ARMOR_ELEC`, `ARMOR_CUT`, `ARMOR_COLD` 等を enchantment 定義から削除する
- **一括削除スクリプト:** `scripts/remove_armor_bullet.py`

### `Name is not an object` / `str_sp not supported`
- **原因:** JSON タイプごとの `name` フィールド形式が厳格化された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:**
  - `ITEM`, `MONSTER`, `SPELL` 等 → `{"str_sp": "名称"}` が必須
  - `overmap_terrain`, `mutation`, `profession` 等 → 単純文字列が必須（`str_sp`/`str_pl` は不可）

### `missing mandatory member "see_cost"`
- **原因:** `overmap_terrain` 型に `see_cost` フィールドが必須化された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** `overmap_terrain` オブジェクトに `"see_cost"` を追加する
- **有効値:** `"none"`, `"low"`, `"medium"`, `"high"`

### `Invalid or misplaced field name "compare_int"`
- **原因:** `compare_int` 条件が EOC で無効化された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** EOC 条件から `compare_int` を削除する

### `rot_spawn` 形式エラー
- **原因:** `rot_spawn` の形式が配列からオブジェクトに変更された（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:**
  - 旧: `[{"monster": "zombie", "probability": 10}]`
  - 新: `{"zombie": 10}`

### `json_flag` 未定義エラー
- **原因:** カスタムフラグを使用する mod で `type: "json_flag"` の定義が欠けている（0.I RC）
- **種別:** rule
- **バージョン:** 0.I RC 以降
- **解決策:** カスタムフラグを `type: "json_flag"` で定義した JSON ファイルを mod に追加する
- **例:**
  ```json
  {
    "type": "json_flag",
    "id": "ONLY_ONE",
    "info": "Only one of this item can be carried."
  }
  ```

---
※ 新しいエラーが発生したらこのファイルに追記する
