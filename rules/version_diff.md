# CDDAバージョン差分メモ

## 0.G → 0.H の主な変更

<a id="unit-string"></a>
### 単位の文字列化（破壊的変更）
- `volume` と `weight` が数値から文字列形式に変更
  - 旧: `"volume": 3`, `"weight": 500`
  - 新: `"volume": "750 ml"`, `"weight": "500 g"`
- 旧modを移植するときは全ての volume / weight フィールドを変換する

### その他（調査中・随時更新）
- 確認した差分はここに追記する

## 0.H → 0.I の主な変更

<a id="recipe-activity_level"></a>
### recipe に `activity_level` が必須化（破壊的変更）
- `recipe` オブジェクトに `activity_level` フィールドが必須になった
- 省略するとゲーム起動時に `missing mandatory member "activity_level"` エラー
- 有効な値: `NO_EXERCISE`, `LIGHT_EXERCISE`, `BRISK_EXERCISE`, `MODERATE_EXERCISE`, `ACTIVE_EXERCISE`
- 旧modを移植するときは全ての recipe に `activity_level` を追加する
  ```json
  { "type": "recipe", "activity_level": "BRISK_EXERCISE", ... }
  ```
- カテゴリ別推奨値:
  - 座り作業・読み書き: `NO_EXERCISE`
  - 軽作業・縫製・調理: `LIGHT_EXERCISE`
  - 金属加工・武器製作: `BRISK_EXERCISE`
  - 重作業・機械組み立て: `MODERATE_EXERCISE`

<a id="field_type"></a>
### field_type の構造変更（破壊的変更）
- `immunity_data` の `traits` → `flags` に変更
  - 旧: `"immunity_data": { "traits": [ "WEB_WALKER" ] }`
  - 新: `"immunity_data": { "flags": [ "WEBWALK" ] }`
- `convection_temperature_mod` の位置変更
  - 旧: `intensity_levels` 内の `effects` 配列の各エフェクトオブジェクトに配置
  - 新: `intensity_levels` 内の各レベルオブジェクトと同じレベル（`effects` の兄弟要素）に配置
- `dangerous`, `translucency`, `effects` 等の位置
  - 旧: `field_type` のルートレベルに配置可能だった
  - 新: `intensity_levels` 配列内の各レベルオブジェクトに配置

<a id="price"></a>
### price / price_postapoc の文字列形式化（破壊的変更）
- `price` と `price_postapoc` が数値形式から通貨文字列形式に変更
  - 旧: `"price": 150`（セント単位の数値）
  - 新: `"price": "1 USD 50 cent"`（通貨文字列）
- 変換ルール:
  - 150 → `"1 USD 50 cent"`
  - 1000 → `"10 USD"`
  - 25 → `"25 cent"`
  - 0 → `"0 cent"`
  - 222000 → `"2 kUSD 220 USD"`

<a id="ammo-type"></a>
### AMMO タイプの統合（破壊的変更）
- `type: "AMMO"` が廃止され、`ITEM` 型に `subtypes` を使う形式に変更
  - 旧: `"type": "AMMO"`
  - 新: `"type": "ITEM", "subtypes": ["AMMO"]`
- その他のサブタイプも同様: `GUN`, `ARMOR`, `TOOL` 等は `ITEM` 型統合の対象
- **注意:** 0.I コアデータ内では `type: "AMMO"` は完全に削除されている。grep してゼロ件であることを確認すること

<a id="armor-ballistic"></a>
### enchantment 旧アーマー値の削除（破壊的変更）
- enchantment 定義から `ARMOR_BALLISTIC`, `ARMOR_ACID`, `ARMOR_BASH`, `ARMOR_BIO`, `ARMOR_STAB`, `ARMOR_HEAT`, `ARMOR_ELEC`, `ARMOR_CUT`, `ARMOR_COLD` 等を削除する
- 一括削除スクリプト: `scripts/remove_armor_bullet.py`

<a id="special_attacks"></a>
### special_attacks の無効化（破壊的変更）
- 特定の `special_attacks` 値が無効化された
  - 無効化された値: `RANGED_PULL`, `GRAB_DRAG`, `SHOCKSTORM`, `STRETCH_ATTACK`, `GRAB`
- `monsters/` 配下の `special_attacks` 配列から該当値を削除する

<a id="see_cost"></a>
### overmap_terrain の see_cost 必須化（破壊的変更）
- `overmap_terrain` 型に `see_cost` フィールドが必須化
- 有効値: `"none"`, `"low"`, `"medium"`, `"high"` 等
- 省略すると `missing mandatory member "see_cost"` エラー

<a id="eoc"></a>
### EOC 条件の変更（破壊的変更）
- `compare_int` 条件が無効化
  - エラー: `Invalid or misplaced field name "compare_int"`
- `target_params` 内の `search_range` が無効化
  - `target_params` から `search_range` フィールドを削除する
- **`condition` の boolean 条件は文字列で指定する**
  - `"condition": { "u_is_avatar": true }` → 誤り（`unrecognized condition` エラー）
  - `"condition": "u_is_avatar"` → 正しい（裸の文字列）
  - 同様に: `"u_is_npc"`, `"u_is_character"`, `"u_is_outside"`, `"u_is_alive"`, `"u_is_deaf"`, `"u_is_underwater"` 等も文字列形式
  - 実装例: `external/cdda/data/mods/MindOverMatter/`, `external/cdda/data/mods/Xedra_Evolved/` 等で多数使用

<a id="rot_spawn"></a>
### rot_spawn 形式変更（破壊的変更）
- `rot_spawn` の形式が配列からオブジェクトに変更
  - 旧: `{"monster": "zombie", "probability": 10}` の配列
  - 新: `{"zombie": 10}` のオブジェクト

<a id="rag-migration"></a>
### ITEM ID 統合: `rag` → `sheet_cotton`（破壊的変更）
- 旧 ITEM ID `rag` が `sheet_cotton` に統合された
- 旧 mod 内の `"rag"` 参照は `"sheet_cotton"` に置換する
- 確認方法: `external/cdda/data/json/obsoletion_and_migration_0.I/migration_items.json` に `"id": "rag", "type": "MIGRATION", "replace": "sheet_cotton"` がある
- 他の 0.I 統合 ID 候補: 同ファイルを `grep '"type": "MIGRATION"'` で一覧確認

<a id="vehicle_part"></a>
### vehicle_part フラグ整理（破壊的変更）
- `FENDER` フラグが削除された
  - mud flap 系 vehicle_part は実装不可
  - 確認: `external/cdda/data/json/vehicleparts/vp_flags.json` に `FENDER` エントリなし
- ライト系フラグ（`CONE_LIGHT`, `CIRCLE_LIGHT`, `HEADLIGHT` 等）は電装前提
  - これらを使用するには `ENABLED_DRAINS_EPOWER` フラグと `epower` 数値（負の値: 消費電力）が必要
  - 車両バッテリーが必須のため、序盤〜即席コンセプトの mod では使用不可
- 実装前に必ず `vp_flags.json` で実在確認すること
- 詳細: `rules/patterns/vehicle_part.md`

<a id="json_flag"></a>
### flags.json（json_flag）の新規作成（破壊的変更）
- カスタムフラグを使用する mod は `type: "json_flag"` の定義ファイルが必要
- `modinfo.json` の `dependencies` に関係するフラグを提供する mod が含まれているか確認

<a id="name-format"></a>
### name フィールド形式の厳格化（破壊的変更）
- `ARMOR` / `TOOL` / `GUN` / `GUNMOD` / `MAGAZINE` / `BIONIC_ITEM` / `SPELL`: `{"str": "名称"}` が基本（自動生成可能な単数形。`str_pl` を付けると不要エラー）
- `COMESTIBLE` / `FOOD` / `DRINK`: `{"str_sp": "名称"}` が基本（単複同形・不可算寄り）。ただし可算の医薬品等で `{"str": "..."}` も可
- 自動生成できない語（cuirass等）・`pair of ...`: `{"str": "...", "str_pl": "..."}` が必須
- `MONSTER`: 単純文字列 → `{"str": "..."}` が必須（一部モンスターでは `{"str_sp": "..."}` も使用可）
- `overmap_terrain`, `mutation`, `profession` 等: `{"str_sp": "..."}` → 単純文字列が必須
- 形式が合わないと `Name is not an object` または `str_sp not supported` エラー
- 詳細は `rules/CORE.md`「name フィールド形式（0.I RC）」節に準拠すること

<a id="text-style"></a>
### テキストスタイルチェッカーの導入（破壊的変更）
- 英語テキストの `.` `!` `?` の後に半角スペースが2つ必須になった
- 文中の句読点後にスペースが1つしかない場合、`insufficient spaces at this location.  2 required, but only 1 found.` エラー
- 対象: 全JSONファイル内の英文文字列（`description`, `name`, `sound`, `done_message` 等）
- 解決策: 対象の句読点の後にスペースを1つ追加する
  - 例: `"Hulk. High"` → `"Hulk.  High"`
  - 例: `"CLANK! CLANK!"` → `"CLANK!  CLANK!"`

### その他（調査中）
- `external/cdda/doc/` の changelog やリリースノートを確認して随時追記する
- 変更確認コマンド:
  ```bash
  grep -r "TODO\|CHANGED\|DEPRECATED" external/cdda/doc/ | head -30
  ```

## バージョン確認方法
- `external/cdda/data/version.json` または `external/cdda/VERSION` を確認する