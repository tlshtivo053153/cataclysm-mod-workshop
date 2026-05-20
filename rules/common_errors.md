# よくあるエラーと解決策

このファイルはゲーム起動時・JSON読み込み時に発生するエラーの**即座の解決策**に焦点を当てています。各変更の背景や詳細なバージョン差分は [`version_diff.md`](version_diff.md) を参照してください。

---

## エラー一覧

### `unknown type: XXX`
- **原因:** `type` フィールドの値のスペルミス
- **解決策:** `external/cdda/data/json/` で正しい type 名を検索して確認する
- **例:** `"type": "GENRIC"` → `"type": "GENERIC"`

### `can't find copy_from target 'XXX'`
- **原因:** `copy-from` で指定したIDが存在しない
- **解決策:**
  1. `external/cdda/data/json/` でIDを grep して存在確認する
  2. 依存modが `dependencies` に記載されているか確認する
  3. IDのスペルミスを確認する

### `JSON parse error` / `unexpected token`
- **原因:** JSONの構文エラー
- **解決策:** `scripts/validate.sh` を実行してエラー行を確認する。末尾カンマ、括弧の対応を確認する

### `missing required field: XXX`
- **原因:** 必須フィールドが欠けている
- **解決策:** `external/cdda/doc/JSON/JSON_INFO.md` で該当 type の必須フィールドを確認する

---

## 0.I 移植時の頻出エラー（バージョン固有）

以下は 0.H → 0.I への移植時に頻出するエラーです。詳細な背景・変換例は [`version_diff.md`](version_diff.md) を参照。

### `missing mandatory member "activity_level"`
- **解決策:** recipe オブジェクトに `"activity_level"` を追加する
- **有効な値:** `"NO_EXERCISE"`, `"LIGHT_EXERCISE"`, `"BRISK_EXERCISE"`, `"MODERATE_EXERCISE"`, `"ACTIVE_EXERCISE"`
- **一括変換スクリプト:** `scripts/add_activity_level.py`
- **詳細:** [`version_diff.md#recipe-activity_level`](version_diff.md)

### `Invalid or misplaced field name "traits" in JSON data` (field_type)
- **解決策:** `"immunity_data": { "traits": ["XXX"] }` → `"immunity_data": { "flags": ["XXX"] }`
- **詳細:** [`version_diff.md#field_type`](version_diff.md)

### `Invalid or misplaced field name "convection_temperature_mod"` (field_type)
- **解決策:** `intensity_levels` 内の `effects` 配列から外し、同じレベルオブジェクトの兄弟要素として配置する
- **詳細:** [`version_diff.md#field_type`](version_diff.md)

### `Invalid or misplaced field name "dangerous" / "translucency" / "effects"` (field_type)
- **解決策:** これらのフィールドを `intensity_levels` 配列内の各レベルオブジェクトに移動する
- **詳細:** [`version_diff.md#field_type`](version_diff.md)

### `bound_reader failed to read value` / `price`
- **解決策:** 数値を通貨文字列に変換する
- **例:** `"price": 150` → `"price": "1 USD 50 cent"`
- **一括変換スクリプト:** `scripts/convert_price.py`
- **詳細:** [`version_diff.md#price`](version_diff.md)

### `unrecognized JSON object` / `type: "AMMO"`
- **解決策:** `"type": "AMMO"` → `"type": "ITEM", "subtypes": ["AMMO"]`
- **対象タイプ:** `AMMO`, `GUN`, `ARMOR`, `TOOL`, `TOOLMOD`, `TOOL_ARMOR`, `BOOK`, `COMESTIBLE`, `ENGINE`, `WHEEL`, `GUNMOD`, `MAGAZINE`, `GENERIC`, `BIONIC_ITEM` 等
- **一括変換スクリプト:** `scripts/convert_item_types.py`
- **詳細:** [`version_diff.md#ammo-type`](version_diff.md)

### `Invalid enum string 'ARMOR_BALLISTIC'`
- **解決策:** `ARMOR_BALLISTIC`, `ARMOR_ACID`, `ARMOR_BASH`, `ARMOR_BIO`, `ARMOR_STAB`, `ARMOR_HEAT`, `ARMOR_ELEC`, `ARMOR_CUT`, `ARMOR_COLD` 等を enchantment 定義から削除する
- **一括削除スクリプト:** `scripts/remove_armor_bullet.py`
- **詳細:** [`version_diff.md#armor-ballistic`](version_diff.md)

### `Name is not an object` / `str_sp not supported`
- **解決策:**
  - `ITEM`, `MONSTER`, `SPELL` 等 → `{"str_sp": "名称"}` が必須
  - `overmap_terrain`, `mutation`, `profession` 等 → 単純文字列が必須
- **詳細:** [`version_diff.md#name-format`](version_diff.md)

### `missing mandatory member "see_cost"`
- **解決策:** `overmap_terrain` オブジェクトに `"see_cost"` を追加する
- **有効値:** `"none"`, `"low"`, `"medium"`, `"high"`
- **詳細:** [`version_diff.md#see_cost`](version_diff.md)

### `Invalid or misplaced field name "compare_int"`
- **解決策:** EOC 条件から `compare_int` を削除する
- **詳細:** [`version_diff.md#eoc`](version_diff.md)

### `rot_spawn` 形式エラー
- **解決策:** 配列形式からオブジェクト形式へ変更
  - 旧: `[{"monster": "zombie", "probability": 10}]`
  - 新: `{"zombie": 10}`
- **詳細:** [`version_diff.md#rot_spawn`](version_diff.md)

### `json_flag` 未定義エラー
- **解決策:** カスタムフラグを `type: "json_flag"` で定義した JSON ファイルを mod に追加する
- **詳細:** [`version_diff.md#json_flag`](version_diff.md)

### volume/weight の値が不正
- **解決策:** 数値から文字列形式に変換する
  - 旧: `"volume": 3`, `"weight": 500`
  - 新: `"volume": "750 ml"`, `"weight": "500 g"`
- **詳細:** [`version_diff.md#単位の文字列化`](version_diff.md)

---

## 無効フィールドの削除

debug.log などで `Invalid or misplaced field name "XXX"` が大量に出る場合、[`rules/invalid_fields.json`](invalid_fields.json) に定義された既知の無効フィールドを一括削除できます。

- **一括削除スクリプト:** `scripts/remove_invalid_fields.py`
- **フィールド定義:** `rules/invalid_fields.json`
- **使い方:**
  ```bash
  python scripts/remove_invalid_fields.py --input ./mods/my_mod/
  ```

---

※ 新しいエラーが発生したらこのファイルに追記する
