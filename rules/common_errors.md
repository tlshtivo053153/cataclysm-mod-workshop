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

### talk_topic response の `condition` で選択肢が表示されない
- **原因:** `u_has_var` で変数をチェックしている。`u_has_var` は talk_topic の condition パーサーに**登録されていない無効なキーワード**であり、未認識キーワードは常に false を返す（`src/condition.cpp`）。`u_has_trait`, `u_has_item` 等の他の `u_has_*` キーワードは有効だが、`u_has_var` はパーサーテーブルに存在しない。文字列変数（`u_add_var`）に対しても機能しない。
- **背景:** math 変数（`{ "math": [ "u_xxx = value" ] }`）と `u_add_var` で設定した文字列変数は、CDDA 内部では**同じ `values` マップ**に格納される（`src/creature.h:1258`）。したがってどちらの変数も `{ "math": [...] }` 形式でチェック可能であり、区別する必要はない。
- **解決策:** `condition` 内では `{ "math": [ "u_var == value" ] }` 形式を使用する。
  - 誤: `"condition": { "u_has_var": "wm_can_melee" }`
  - 正: `"condition": { "math": [ "u_wm_can_melee == 1" ] }`
- **参照:** `rules/patterns/eoc.md` の「推奨パターン: talk_topic response の `condition` で動的フィルタリング + 単一トピック + trial 判定」

### talk_topic response で `topic` 省略時に effect が実行されない
- **現象:** response の `topic` を省略すると、`effect` 配列内の `set_string_var`、`u_message`、`open_dialogue` 等がすべて**無視**され、親トピックに戻る。エラーメッセージは出ない（サイレント失敗）。
- **原因:** `topic` 未指定時は次のトピックへの遷移が発生せず、会話エンジンが effect を処理しない。
- **解決策:** response には必ず `"topic"` を明示する。`open_dialogue` で新規会話を開く場合も、元の会話を維持するために `"topic"` で戻り先を指定すること。
  - 誤: `"topic"` 省略 → effect 未実行
  - 正: `"topic": "TALK_CURRENT_MENU"` 等で明示的に戻り先を指定
- **参照:** `rules/patterns/eoc.md` の「talk_topic response effect 内の `open_dialogue` と context_val の制約」

---


## 0.I 移植時の頻出エラー（バージョン固有）

以下は 0.H → 0.I への移植時に頻出するエラーです。詳細な背景・変換例は [`version_diff.md`](version_diff.md) を参照。

### `missing mandatory member "activity_level"`
- **解決策:** recipe オブジェクトに `"activity_level"` を追加する
- **有効な値:** `"NO_EXERCISE"`, `"LIGHT_EXERCISE"`, `"BRISK_EXERCISE"`, `"MODERATE_EXERCISE"`, `"ACTIVE_EXERCISE"`
- **一括変換スクリプト:** `scripts/add_activity_level.py`
- **詳細:** [`version_diff.md#recipe-activity_level`](version_diff.md#recipe-activity_level)

### `Invalid or misplaced field name "traits" in JSON data` (field_type)
- **解決策:** `"immunity_data": { "traits": ["XXX"] }` → `"immunity_data": { "flags": ["XXX"] }`
- **詳細:** [`version_diff.md#field_type`](version_diff.md#field_type)

### `Invalid or misplaced field name "convection_temperature_mod"` (field_type)
- **解決策:** `intensity_levels` 内の `effects` 配列から外し、同じレベルオブジェクトの兄弟要素として配置する
- **詳細:** [`version_diff.md#field_type`](version_diff.md#field_type)

### `Invalid or misplaced field name "dangerous" / "translucency" / "effects"` (field_type)
- **解決策:** これらのフィールドを `intensity_levels` 配列内の各レベルオブジェクトに移動する
- **詳細:** [`version_diff.md#field_type`](version_diff.md#field_type)

### `bound_reader failed to read value` / `price`
- **解決策:** 数値を通貨文字列に変換する
- **例:** `"price": 150` → `"price": "1 USD 50 cent"`
- **一括変換スクリプト:** `scripts/convert_price.py`
- **詳細:** [`version_diff.md#price`](version_diff.md#price)

### `unrecognized JSON object` / `type: "AMMO"`
- **解決策:** `"type": "AMMO"` → `"type": "ITEM", "subtypes": ["AMMO"]`
- **対象タイプ:** `AMMO`, `GUN`, `ARMOR`, `TOOL`, `TOOLMOD`, `TOOL_ARMOR`, `BOOK`, `COMESTIBLE`, `ENGINE`, `WHEEL`, `GUNMOD`, `MAGAZINE`, `GENERIC`, `BIONIC_ITEM` 等
- **一括変換スクリプト:** `scripts/convert_item_types.py`
- **詳細:** [`version_diff.md#ammo-type`](version_diff.md#ammo-type)

### `Invalid enum string 'ARMOR_BALLISTIC'`
- **解決策:** `ARMOR_BALLISTIC`, `ARMOR_ACID`, `ARMOR_BASH`, `ARMOR_BIO`, `ARMOR_STAB`, `ARMOR_HEAT`, `ARMOR_ELEC`, `ARMOR_CUT`, `ARMOR_COLD` 等を enchantment 定義から削除する
- **一括削除スクリプト:** `scripts/remove_armor_bullet.py`
- **詳細:** [`version_diff.md#armor-ballistic`](version_diff.md#armor-ballistic)

### `Name is not an object` / `str_sp not supported`
- **解決策 (0.I RC, `rules/CORE.md`「name フィールド形式（0.I RC）」節に準拠):**
  - `ARMOR` / `TOOL` / `GUN` / `GUNMOD` / `MAGAZINE` / `BIONIC_ITEM` / `SPELL` → `{"str": "名称"}` が基本（自動生成可能な単数形。可算名詞のinjector等もこちら）
  - `COMESTIBLE` / `FOOD` / `DRINK` → `{"str_sp": "名称"}` が基本（単複同形・不可算寄り）。ただし可算の医薬品等で `{"str": "..."}` も可（親 `adrenaline_injector` は `str` 形式）
  - 自動生成できない語（cuirass等）→ `{"str": "...", "str_pl": "..."}`、`pair of ...` は `str_pl` 必須
  - `MONSTER` → `{"str": "名称"}`（バニラで支配的な形式）。一部モンスターでは `{"str_sp": "..."}` も使用可
  - `overmap_terrain`, `mutation`, `profession` 等 → 単純文字列が必須
- **詳細:** [`version_diff.md#name-format`](version_diff.md#name-format)

### `missing mandatory member "see_cost"`
- **解決策:** `overmap_terrain` オブジェクトに `"see_cost"` を追加する
- **有効値:** `"none"`, `"low"`, `"medium"`, `"high"`
- **詳細:** [`version_diff.md#see_cost`](version_diff.md#see_cost)

### `Invalid or misplaced field name "compare_int"`
- **解決策:** EOC 条件から `compare_int` を削除する
- **詳細:** [`version_diff.md#eoc`](version_diff.md#eoc)

### `open_dialogue` の書式エラー（EOC）

- **現象:** debug.log に `Unread data.  Invalid or misplaced field name "open_dialogue" in JSON data` と表示される
- **原因:** EOC effect 内の `open_dialogue` に裸の文字列を指定している
- **解決策:** `"open_dialogue"` の値は **`topic` キーを持つオブジェクト**で指定する
  - 誤: `{ "open_dialogue": "TALK_MY_DIALOGUE" }`
  - 正: `{ "open_dialogue": { "topic": "TALK_MY_DIALOGUE" } }`
- **参照:** `rules/patterns/eoc.md` の「`open_dialogue` の構文」節

### `clamp()` の `lo > hi` による未定義動作・クラッシュリスク

- **現象:** CDDA の math 式で `clamp(x, lo, hi)` の `lo > hi` を指定すると、未定義動作によりクラッシュする可能性がある
- **原因:** CDDA の `clamp` 実装は `hi > lo` を前提としており、範囲が逆転している場合の動作は保証されない
- **解決策:** `clamp()` を使用する場合は常に `hi > lo` を保証する。エッジケーステストや意図的な逆転は行わない
  - 正: `clamp(15, 0, 10)` → 10
  - テスト不可: `clamp(5, 10, 0)` → 未定義動作・クラッシュリスク
- **参照:** CDDA ドキュメント（`math` 関数リファレンス）で `clamp` の引数順序を確認する

### 表示テキスト内の `＜` `＞` による `Bad tag` エラー・テキスト途切れ

- **現象:** debug.log に `DEBUG : Bad tag. '<...>'` が表示される、または `u_message` / talk_topic の `text` / `dynamic_line` のテキストが途中で途切れる
- **原因:** CDDA のタグパーサ（`src/npctalk.cpp:2607` `parse_tags`）が表示テキスト内の半角 `<` をタグ開始、半角 `>` をタグ終了と解釈する。比較演算子 `＜`, `＞`, `＜=`, `＞=` を含む文字列が誤ってタグとして処理される
- **対象:** `u_message`, talk_topic の `text` / `dynamic_line` 等、画面に表示されるすべての文字列
- **影響を受けないもの:** math 式文字列（`"u_test_a < 5"`）、condition 内の式。これらはタグパーサを通らない
- **解決策:** 表示テキスト内の半角 `<` `>` を全角 `＜`（U+FF1C）`＞`（U+FF1E）に置換する
  - 誤: `"[MATH COMPARE] lt (5<10): <u_val:test_lt> (expect 1)"`
  - 正: `"[MATH COMPARE] lt (5＜10): <u_val:test_lt> (expect 1)"`
  - 誤: `"math >= 40（条件を満たす場合のみ表示）"`
  - 正: `"math ＞= 40（条件を満たす場合のみ表示）"`
- **注意:** `<u_val:xxx>`, `<context_val:xxx>`, `<npc_val:xxx>` 等の正当なタグは半角 `<` `>` のまま維持すること。置換対象は比較演算子としての `<` `>` のみ
- **参照:** `rules/patterns/eoc.md` の「表示テキスト内の `<` `>` 文字の全角化」

### `rot_spawn` 形式エラー
- **解決策:** 配列形式からオブジェクト形式へ変更
  - 旧: `[{"monster": "zombie", "probability": 10}]`
  - 新: `{"zombie": 10}`
- **詳細:** [`version_diff.md#rot_spawn`](version_diff.md#rot_spawn)

### `json_flag` 未定義エラー
- **解決策:** カスタムフラグを `type: "json_flag"` で定義した JSON ファイルを mod に追加する
- **詳細:** [`version_diff.md#json_flag`](version_diff.md#json_flag)

### volume/weight の値が不正
- **解決策:** 数値から文字列形式に変換する
  - 旧: `"volume": 3`, `"weight": 500`
  - 新: `"volume": "750 ml"`, `"weight": "500 g"`
- **詳細:** [`version_diff.md#unit-string`](version_diff.md#unit-string)

### `charges expected but not defined or <= 0`
- **原因:** `phase: liquid` の液体アイテム等、`charges` を必要とするアイテムで `charges` が定義されていないか、値が0以下になっている
- **解決策:** `charges` フィールドを追加し、正の整数を設定する
- **詳細:** 液体 COMESTIBLE では `charges` が必須。バニラの `coffee`（`charges: 1`）、`bleach`（`charges: 2`）等を参照

### `charges defined but can not have any`
- **原因:** `charges` を持てないアイテム（`phase: solid` や `phase` 未定義の固体等）に `charges` を定義している
- **解決策:** `charges` フィールドを削除する
- **詳細:** `charges` の使用可否は主に `phase`（液体か固体か）で決まる。`phase: liquid` の液体アイテムでは `charges` が必須的に使われる一方、`phase: solid` や液体でないアイテムでは `charges` を持てない。バニラの `coffee`（液体、`charges: 1`）と `granola`（固体、`charges` なし）を参照

### `Invalid surface_heat format`
- **原因:** recipe の `tools` で `surface_heat` を `["surface_heat", N, "C"]` のように指定している
- **解決策:** 必ず `"LIST"` を使用する → `["surface_heat", N, "LIST"]`
- **例:** `bread` レシピでは `["surface_heat", 22, "LIST"]`、`granola` では `["surface_heat", 20, "LIST"]`
- **詳細:** `"C"`（セルシウス温度）形式は存在しない

### recipe components で AMMO アイテムのチャージ数が不明

- **原因:** `duct_tape`（`ammo_type: "tape"`）や `chem_carbide`（`ammo_type: "components"`）等の AMMO アイテムをレシピ材料にする際、消費チャージ数の指定方法が不明瞭
- **解決策:** `components` 内で `[ "item_id", N ]` の形式で指定する。`ammo_type` の指定は不要
- **例:** `[ "duct_tape", 10 ]` → 10チャージ消費。`[ "chem_carbide", 20 ]` → 20チャージ消費
- **注意:** `ammo_type: "components"` のアイテムは弾薬ではないが、AMMO subtype としてチャージ数を持つ。レシピでの消費方法は通常の AMMO と同様

### `recipe X is nested but isn't in a nested group`
- **原因:** `subcategory: "CSC_*_NESTED"` のレシピが、いずれの `nested_category` の `nested_category_data` にも含まれていない
- **解決策:** `type: "nested_category"` を定義し、レシピIDを `nested_category_data` 配列に追加する
- **制約:** バニラの `nested_category` に `extend` で追加することはできない（`nested_category_data` は `mandatory()` で読み込まれるため）。必ず独自の nested_category を新規定義する
- **詳細:** `rules/patterns/recipe_nested.md`

### `item group "XXX" already defined with type "collection"`
- **原因:** `copy-from` + `extend` で collection 型の item_group を拡張しようとしたが、子側で `"subtype": "collection"` を宣言していない
- **解決策:** 子側の定義に `"subtype": "collection"` を明示的に追加する。または拡張先を distribution 型の item_group に変更する
- **制限:** CDDA 0.I では collection 型の item_group を `copy-from` で拡張する場合、子側で `"subtype": "collection"` の再宣言が必要（distribution 型の拡張では不要）
- **例:** `lab_mutagen_ingredients_fridge`（collection 型）を extend する場合、`"subtype": "collection"` を追記すれば可。distribution 型の `science` への extend であれば subtype 宣言不要で可
- **参考:** Magiclysm 公式mod `external/cdda/data/mods/Magiclysm/itemgroups/` — collection 型の拡張では必ず `"subtype": "collection"` を再宣言している（death_drops.json の `feral_humans_death_drops_axe` 等）

### `insufficient spaces at this location.  2 required, but only 1 found.`
- **原因:** CDDA 0.I のテキストスタイルチェッカーが英語テキストの句読点（`.` `!` `?`）の後に2スペースを要求
- **対象:** 英文文字列内の文中の句読点。文字列末尾の句読点は対象外
- **解決策:** 対象の句読点の後に半角スペースを追加する
  - 例: `"Hulk. High"` → `"Hulk.  High"`
  - 例: `"CLANK! CLANK!"` → `"CLANK!  CLANK!"`
- **注意:** 日本語テキストには適用されない。英文のみが検査される
- **詳細:** [`version_diff.md#text-style`](version_diff.md#text-style)

### `vehicle part X is not CARGO and cannot define size`
- **原因:** `vehicle_part` に `size` フィールドがあるが `CARGO` フラグが付いていない
- **解決策:**
  1. CARGO フラグを追加する（`flags: [..., "CARGO"]`）
  2. または `size` フィールドを削除する（`BED`, `SEAT` 等のサイズ指定は意味を持たない）
- **詳細:** `rules/patterns/vehicle_part.md`

### `Invalid or misplaced field name "ammo"` (TOOL アイテム)
- **原因:** `"subtypes": ["TOOL"]` のアイテムに `"ammo"` フィールドを定義
- **解決策:** トップレベルの `ammo` は `TOOL`・`AMMO` subtype では無効。`AMMO`品が持つのは `ammo_type` であり、`ammo: [...]` を持つのは `GUN` を含む subtype のみ。有効な文脈は `GUN`（例: `ammo: ["arrow"]`）、`item_group` の数値指定、`vehicle_part`、mapgen の `spawn_data`、モンスター繁殖定義等。文脈を確認して削除可否を判断する（`scripts/remove_invalid_fields.py` は再帰削除による正規GUN破壊を避けるため `remove_always` に含めず温存する）
- **正しい AMMO 定義:**
  ```json
  { "type": "ITEM", "subtypes": ["AMMO"], "id": "...", "ammo_type": "battery", "count": 100 }
  ```
- **詳細:** `rules/patterns/vehicle_part.md`

### `itemgroup entry for spawning item X defined charges but can't have any` (vehicle_part breaks_into)
- **原因:** `vehicle_part.breaks_into` で charge 非対応アイテムに `charges` を指定
- **charge 非対応の代表例:** `wire`, `splinter`（GENERIC ITEM で subtype 未定義。`max_charges` 設定なし）
- **charge 対応の代表例:** `nail`, `scrap`（AMMO subtype）、`plastic_chunk`（TOOL subtype で `max_charges` 設定なしなら非対応、設定済なら対応）
- **解決策:** `charges` を `count` に変更する
  - 例: `{"item": "wire", "charges": [4, 10]}` → `{"item": "wire", "count": [1, 3]}`
- **詳細:** `rules/patterns/vehicle_part.md`

### `unknown vehicle part flag "FENDER"`
- **原因:** 0.I で削除された `vehicle_part` フラグを使用
- **0.I で削除されたフラグ:** `FENDER`（mud flap 系）
- **事前確認:** 実装前に `external/cdda/data/json/vehicleparts/vp_flags.json` で実在確認する
- **解決策:** フラグを削除する、または別フラグに置換する
- **詳細:** `rules/patterns/vehicle_part.md`

### `skills_required` の書式（単一スキル / 複数スキル）
- **原因:** 単一スキルと複数スキルで書式の使い分けが必要
- **解決策:**
  - 単一スキルの場合はフラット配列: `"skills_required": ["gun", 2]`
  - 複数スキルの場合は入れ子配列: `"skills_required": [["traps", 1], ["gun", 1]]`
- **注意:** バニラCDDA（`ranged.json` 等）では両方の書式が混在しており、いずれも有効。単一スキルか複数スキルかで使い分ける

### GUNMODが装着できない（mod_targets が狭すぎる）
- **原因:** `mod_targets` が限定されすぎている。例：`mod_targets: ["rifle"]` だけだと、実際に該当 `location` を持つ銃が少なく装着不可になる
- **解決策:** バニラ同種GUNMOD（例: `bipod`）の `mod_targets` を参照し、同等の広さに拡張する
  - 例: `["rifle"]` → `["rifle", "launcher", "smg", "shotgun", "crossbow"]`
- **注意:** また `"underbarrel"` と `"underbarrel mount"` は別スロット。前者は直接装着スロットで一部の銃のみ持つ。後者はアダプター用スロットで多くの最新銃が持つ。`underbarrel_mount` アダプターを経由すれば間接装着可能

### trap action のハードコード制限（既知の制約）
- **原因:** C++ 実装の trap action がドロップアイテムやメッセージをハードコードしている
- **具体例:**
  - `action: "snare_light"` → トリガー時に **常に `light_snare_kit` をドロップ**する。`drops` フィールドは無視される
  - `action: "bubble"` → 踏んだ時のメッセージとサウンドがハードコードされ、変更不可
- **影響:** これらの action を `copy-from` や `drops` フィールドでカスタマイズしても、C++ 側の動作は変わらない
- **回避策:** 詳細は `rules/patterns/trap.md` 参照

---

## よくあるエラー（変異・エンチャント関連）

### mutation_type の不正な値
- **原因**: `types` フィールドに未定義の値を指定している
- **解決策**: 有効値は `external/cdda/data/json/mutations/mutation_type.json` に定義されたもののみ
- **よくある間違い**: `SMELL` → `SCENT`, `ATTACK` → `SECRETION`

### enchantment value の未定義エラー
- **原因**: enchantmentの `values` に存在しない value 名を指定している
- **解決策**: `external/cdda/data/json/` の enchantment 定義を確認する
- **よくある間違い**:
  - `PAIN_RESIST` は未定義 → `PAIN` + multiply: -0.25 で代用
  - `ARMOR_BALLISTIC`, `ARMOR_ACID` 等の旧防具フラグは enchantment では使えない

### comfort 条件の不正なtype
- **原因**: comfort フィールドの `condition.type` に無効な値を指定している
- **解決策**: 有効値は `terrain`, `field`, `vehicle`, `furniture`, `trait` のみ
- **よくある間違い**: `npc_following` → 存在しないtype。

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

## mapgen・mapgen_palette 関連エラー

### mapgen `rows` のカンマ文字による silent error / タイムアウト
- **現象:** `check_mods.sh` がタイムアウト（デフォルト90秒）、または debug.log に `mapgen.cpp:5365 setup_common` エラーが大量発生するがエラーメッセージが空
- **原因:** mapgen の `rows` 文字列内で `,`（カンマ）を未マップ文字として使用している。カンマは CDDA 内部で特別な扱いを受ける文字であり、パレットで明示的に terrain マッピングされていない場合 `fill_ter` が適用されずエラーになる（`.` は `fill_ter` が適用される）
- **解決策:** `rows` 内の `,` を `.` に置換する。`.` は `fill_ter` でカバーされる安全な文字。または `,` をパレットの `terrain` で明示的にマッピングする（例: `",": "t_region_soil"` — `shelter_unfinished` パレットのパターン）
- **注意:** `validate.sh` では検出できない。24文字の行長が合っていてもエラーになる

### roof_palette の未定義文字 / 文字競合
- **現象:** `check_mods.sh` で屋根 mapgen がエラー。debug.log に `roof_palette` を使った mapgen の `setup_common` エラー
- **原因:**
  1. `*`（ladder up）は `roof_palette` の terrain に定義されていない（`shelter` パレットでは定義されている）
  2. `~` は `roof_palette` の furniture で `f_chimney`（煙突）にマップされている
- **解決策:** 屋根 mapgen の `object` 内でインライン `terrain` / `furniture` 定義を追加して上書きする:
  ```json
  "terrain": { "*": "t_ladder_up" },
  "furniture": { "~": "f_sandbag_half" }
  ```
- **事前確認:** `external/cdda/data/json/mapgen_palettes/roof_palette.json` で使用予定文字のマッピングを確認する

### mapgen rows の行長エラー（24x24不一致）
- **現象:** マップ生成時に壁の繋がりが崩れたり、タイル位置がずれる
- **原因:** 24x24グリッドの各行文字列が正確に24文字になっていない
- **解決策:** Python 等で全行の `len(row)` を確認する:
  ```bash
  python3 -c "import json; d=json.load(open('file.json')); [print(f'row[{i}] len={len(r)}') for e in d for i,r in enumerate(e.get('object',{}).get('rows',[])) if len(r)!=24]"
  ```
- **注意:** `validate.sh` では検出できない。1文字のズレが建物全体のレイアウトを破壊する

### パレット継承時の文字競合
- **現象:** 意図しない furniture/terrain が配置される
- **原因:** 継承元パレット（`parametrized_walls_palette`, `shelter` 等）が特定の文字を既にマッピングしている
- **解決策:**
  1. 継承元パレットの全文字マッピングを `external/cdda/data/json/mapgen_palettes/` で事前確認する
  2. 競合する文字は避けるか、`object` 内のインライン `terrain` / `furniture` で上書きする
  3. 新規パレットで継承元の文字を上書きする場合は、`terrain` / `furniture` に明示的に定義する（自パレットの定義は継承元より後に適用されるため優先される）
- **代表的な競合:** `roof_palette` の `~`=`f_chimney`, `shelter` の `:`=`t_window_domestic`, `=`=`t_door_locked_interior` 等
- **補足:** `palettes` 配列に複数のパレットを指定した場合、後方のパレットが前方の定義を上書きする（後勝ち）。`parametrized_walls_palette` を配列末尾に置くことで、他パレットによる `#` / `|` の誤上書きを防止できる

---

※ 新しいエラーが発生したらこのファイルに追記する
