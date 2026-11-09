## Mod設計書: Scrap Boat（廃材ボート）

### 仕様書から継承
- **目的**: 序盤に「都市の廃材で即席のいかだを組む」体験を追加する。専用部品3種は fabrication 1 で作れるが、耐久・速度・積載効率はバニラ同等品より劣る。既存 vehicle システムの拡張のみで、新ゲームシステムは追加しない。
- **スコープ**:
  - 含むもの: 専用 vehicle_part 3種＋設置 ITEM 3点＋レシピ 3点。バニラ流用（`frame_wood` ×4、`seat` ×1）。
  - 含まないもの: 新mapgen、NPC、モンスター、シナリオ、職業、開始地点、完成車プロトタイプ、専用フレーム/シート、エンジン/帆/電装/武器/装甲/折りたたみ、既存車両・既存レシピの改変。
- **成功基準**: 専用3種・6個をクラフトし、`frame_wood` ×4＋`seat` ×1 の2x2いかだに装着して浮上・移動・積載。製作は fabrication 1、装着は既存 vehicle 要件。Level1/Level2 通過、Level3で組立・浮上・移動・積載・脱着・修理・セーブ/ロード確認。速度は `canoe` 以下、船体耐久は `raft_board` 以下、素材は都市廃材で完結。

### ターゲットバージョン
- CDDA: 0.I RC
- 参照データ: `external/cdda` build 2026-04-15-1311（commit `46730b6e7a9ed1c5eebf065a40760183d8d39fc2`）

### 依存関係
- 依存mod: dda（必須）

### modinfo.json
- `type`: `MOD_INFO`
- `id`: `scrap_boat`（ディレクトリ名と一致）
- `name`: `Scrap Boat`
- `authors`: `[ "cdda_mod_framework" ]`
- `description`: `Adds craftable scrap hulls, paddles, and cargo nets for building an early-game raft.`
- `category`: `vehicles`
- `dependencies`: `[ "dda" ]`
- `version`: `1.0`

### 使用予定ID一覧
| 種別 | ID | copy-from | 説明 |
|---|---|---|---|
| vehicle_part | `sb_hull` | `raft_board` | 廃材ポンツーン船体。durability 24、DR 4。FLOATS・hull・under は親継承 |
| vehicle_part | `sb_paddle` | `hand_paddles` | 廃材パドル。power 560 W、durability 35、DR 4 |
| vehicle_part | `sb_cargo` | `basketsm_abstract` | 廃材カーゴネット。size 30 L、durability 40、DR 2 |
| ITEM | `sb_hull_item` | `raft_board` | 船体設置アイテム。material plastic/wood、6.5 kg |
| ITEM | `sb_paddle_item` | `hand_paddles` | パドル設置アイテム。5 kg / 12 L |
| ITEM | `sb_cargo_item` | `bike_basket` | カーゴ設置アイテム。300 g / 1 L |
| recipe | `sb_hull_item` | — | `result` が識別子。1件 |
| recipe | `sb_paddle_item` | — | 同上。1件 |
| recipe | `sb_cargo_item` | — | 同上。1件 |

命名規約: 全IDは `sb_` 接頭辞。`recipe.result` は ITEM ID、vehicle_part.item も同じ ITEM ID。0.I の通常レシピに `id` フィールドは付けない。`basketsm_abstract` は `abstract`（`id` なし）のため `copy-from` 継承可。レシピ3件は既存 `type: recipe` の新規定義のため `copy-from` 不要。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/vehicleparts/vehicle_parts.json` — `raft_board`（durability 30、DR 5、FLOATS、install fab 1＋rope_natural_short 2、removal fab 1＋CUT 2、repair fab 2＋rope_natural_short 1）、`boat_board`（durability 40、DR 10）、`plastic_boat_hull`（durability 120、DR 12）
- [x] `external/cdda/data/json/vehicleparts/manual.json` — `engine_manual`（fuel_type muscle、m2c 45、exclusions manual）、`hand_paddles`（copy-from engine_manual、power 720 W、muscle_power_factor 40、noise 8、durability 50、DR 5、flags ENGINE/CONTROLS/MUSCLE_ARMS/E_STARTS_INSTANTLY、install fab 1 6m、removal fab 2 6m、repair fab 2 60m）
- [x] `external/cdda/data/json/vehicleparts/cargo.json` — `basketsm_abstract`（durability 75、size 20 L、DR 6、CARGO/CARGO_PASSABLE、install mechanics 1＋vehicle_screw、repair mechanics 1/fab 1＋repair_welding_standard）
- [x] `external/cdda/data/json/vehicleparts/frames.json` — `frame_wood`（durability 150、install fab 1＋vehicle_nail_install、removal fab 1＋vehicle_nail_removal、repair fab 2＋adhesive、breaks_into splinter/nail）
- [x] `external/cdda/data/json/items/vehicle/boat.json` — `raft_board`（weight 6000 g、volume 12500 ml、material wood、price 1 USD/10 cent）、`hand_paddles`（weight 8 kg、volume 16 L、material wood、price 90 USD/1 USD）
- [x] `external/cdda/data/json/items/vehicle/cargo.json` — `bike_basket`（copy-from basket、weight 1200 g、volume 5 L、price 35 USD/50 cent）
- [x] `external/cdda/data/json/items/vehicle/frames.json` — `frame_wood`（weight 8000 g、volume 15 L、material wood）
- [x] `external/cdda/data/json/items/vehicle/seating.json` — `seat`（weight 9071 g、volume 7500 ml、material nylon/lc_steel）
- [x] `external/cdda/data/json/recipes/recipe_vehicle.json` — `raft_board`（LIGHT_EXERCISE、fab 2、30 m、log 4＋rope_natural 3 LIST）、`boat_board`（MODERATE、fab 3、1 h、2x4 5＋nail 30）、`plastic_boat_hull`（LIGHT_EXERCISE、fab 4、1 h、plastic_molding 21＋plastic_chunk 18）、`hand_paddles`（MODERATE、fab 1、60 m、2x4 4＋nail 10）、`frame_wood`（MODERATE、fab 1、20 m、2x4 5＋nail 20）
- [x] `external/cdda/data/json/recipes/other/parts.json` — `seat`（MODERATE、fab 1、2 h、pipe 4＋spring 2＋nylon 20＋pipe_fittings 4。自作には sewing/welding・proficiency 要のため調達は車両解体が前提）
- [x] `external/cdda/data/json/requirements/materials.json` — `adhesive`、`cordage_short`、`rope_natural_short` 実在
- [x] `external/cdda/data/json/requirements/vehicle.json` — `vehicle_nail_install`、`vehicle_nail_removal`、`vehicle_wrench_2` 実在
- [x] `external/cdda/data/json/vehicleparts/vp_flags.json` — `FLOATS`（各船体がdraftを下げ、sealed heightを上げる。draft < sealed height で浮上）
- [x] `external/cdda/data/json/construction/misc.json` — `constr_veh`（`vehicle_start: true`、mechanics 0、10 m）でフレームから車両を開始可能
- [x] `external/cdda/data/json/construction_group.json` — `start_vehicle_construction` 実在
- [x] `external/cdda/data/json/vehicles/boats.json` — `raft`（2x2、boat_board×4、seat×4、hand_paddles×1）、`canoe`（1x4、boat_board×4、seat×2、hand_paddles×1）を比較対象として確認
- [x] `external/cdda/data/json/materials.json` — `wood`、`plastic`、`cotton` 実在
- [x] `external/cdda/data/json/tool_qualities.json` — `HAMMER`、`CUT` 実在
- [x] `external/cdda/data/json/items/resources/plastic.json` — `plastic_chunk`、`plastic_sheet` 実在
- [x] `external/cdda/data/json/items/resources/wood.json` — `2x4`、`stick`、`splinter` 実在
- [x] `external/cdda/data/json/items/ammo.json` — `duct_tape` 実在（ammo_type tape、charges指定可）
- [x] `external/cdda/data/json/items/generic/string.json` — `string_6` 実在
- [x] `external/cdda/doc/JSON/JSON_INFO.md` — 0.I の ITEM/vehicle_part/recipe 必須フィールド、name/price/weight/volume の書式を確認
- [x] 新規フラグなし（FLOATS は親から継承）

### ファイル構成
```
mods/medium/scrap_boat/
├── modinfo.json
├── spec.md
├── design.md
└── data/
    ├── items.json          # ITEM 3点
    ├── vehicle_parts.json  # vehicle_part 3点
    └── recipes.json        # recipe 3点
```

### 実装順序
1. modinfo.json
2. data/items.json
3. data/vehicle_parts.json
4. data/recipes.json
- 各編集後に Level1。逸脱はその都度 design.md に反映。

### データフロー
```
recipe.result → ITEM → vehicle_part.item
sb_hull_item → sb_hull_item → sb_hull
sb_paddle_item → sb_paddle_item → sb_paddle
sb_cargo_item → sb_cargo_item → sb_cargo
```

### ITEM 詳細
- `sb_hull_item`（copy-from `raft_board`）: name `{ "str": "scrap pontoon hull" }`、material `[plastic, wood]`、weight `6500 g`、volume `12500 ml` 継承、price `1 USD 50 cent`・price_postapoc `25 cent`。symbol/color/category/to_hit/melee_damage は親継承。
- `sb_paddle_item`（copy-from `hand_paddles`）: name `{ "str": "scrap paddle" }`、material `[wood]` 継承、weight `5000 g`、volume `12 L`、price `20 USD`・price_postapoc `50 cent`。
- `sb_cargo_item`（copy-from `bike_basket`）: name `{ "str": "scrap cargo net" }`、material `[cotton, plastic]`、weight `300 g`、volume `1 L`、price `5 USD`・price_postapoc `25 cent`。

### vehicle_part 詳細
- `sb_hull`: copy-from `raft_board`。durability 24（親30より低い）、damage_reduction `{ "all": 4 }`（親5）。item は `sb_hull_item`。requirements を上書き:
  - install: fabrication 1、20 m、using `cordage_short` 2＋`adhesive` 1
  - removal: fabrication 1、15 m、qualities `CUT` 2
  - repair: fabrication 2、15 m、using `cordage_short` 1＋`adhesive` 1
  - breaks_into: `splinter` 8–16＋`plastic_chunk` 2–6（すべて `count`）
  - flags/categories/location/variants は親継承（FLOATS、hull、under）
- `sb_paddle`: copy-from `hand_paddles`。durability 35（親50）、power `560 W`（親720）、damage_reduction `{ "all": 4 }`（親5）。item は `sb_paddle_item`。install/removal は親継承（fab 1 6m / fab 2 6m）、repair のみ fabrication 1・45 m に短縮。flags（ENGINE/CONTROLS/MUSCLE_ARMS/E_STARTS_INSTANTLY）、muscle_power_factor 40、noise_factor 8、m2c 45 は親継承。breaks_into は親の `splinter` 2–4 を継承。
- `sb_cargo`: copy-from `basketsm_abstract`。durability 40（親75）、size `30 L`（親20 L）、damage_reduction `{ "all": 2 }`（親6）。item は `sb_cargo_item`。requirements を上書き:
  - install: fabrication 1、10 m、using `cordage_short` 2
  - removal: fabrication 1、5 m、qualities `CUT` 1
  - repair: fabrication 1、5 m、using `cordage_short` 1
  - breaks_into: `string_6` 2–4＋`plastic_sheet` 1–2（すべて `count`）
  - flags（CARGO/CARGO_PASSABLE）、location center、variants は親継承

### レシピ詳細
共通: `category CC_OTHER`、`subcategory CSC_OTHER_VEHICLE`、`autolearn true`、`activity_level` 必須、`proficiency` なしを意図（バニラ上位品との差別化）。
- `sb_hull_item`: LIGHT_EXERCISE、fab 1、20 m、qualities HAMMER 1、using `cordage_short` 4。components: `2x4`×2、`plastic_chunk`×6、`duct_tape`×20。
- `sb_paddle_item`: MODERATE_EXERCISE、fab 1、30 m、qualities HAMMER 1。components: `2x4`×1、`stick`×1（家具破壊等で都市調達可。Level3で市街調達を確認）、`duct_tape`×10。
- `sb_cargo_item`: LIGHT_EXERCISE、fab 1、20 m、qualities CUT 1。using `cordage_short` 6。components: `plastic_sheet`×2。

### バニラ流用と全体要件（Level3 前提）
| 部品 | 個数 | 装着要件 |
|---|---|---|
| `frame_wood` | 4 | fabrication 1、vehicle_nail_install 1回/枚（要 HAMMER 2、nails 20/枚） |
| `sb_hull` | 4 | fabrication 1、cordage_short 2＋adhesive 1/個 |
| `seat` | 1 | mechanics 1、vehicle_wrench_2 |
| `sb_paddle` | 1 | fabrication 1、6 m |
| `sb_cargo` | 1 | fabrication 1、cordage_short 2 |

- レイアウトは2x2。`(0,0)` に frame＋hull＋seat＋paddle、`(1,0)` に frame＋hull、`(0,1)` に frame＋hull＋cargo、`(1,1)` に frame＋hull。
- 最初のフレームは construction `constr_veh`（Start Vehicle Construction）で設置し、残りは vehicle のフレーム追加で接続する。
- 完成車プロトタイプは追加しない。エンジン・帆は使わない。

### バランス比較
| 項目 | 本mod | バニラ比較 |
|---|---|---|
| 船体 | `sb_hull`: durability 24、DR 4、6.5 kg、fab 1・20 m、都市廃材 | `raft_board`: durability 30、DR 5、6 kg、fab 2・30 m、丸太＋自然ロープ。`boat_board`: durability 40、DR 10、fab 3・1 h、2x4＋釘30。`plastic_boat_hull`: durability 120、DR 12、fab 4・1 h、プラスチック成型 |
| パドル | `sb_paddle`: 560 W、durability 35、5 kg、fab 1・30 m | `hand_paddles`: 720 W、durability 50、8 kg、fab 1・60 m、2x4×4＋釘10 |
| カーゴ | `sb_cargo`: 30 L、durability 40、DR 2、fab 1・20 m | `basketsm`: 20 L、durability 75、DR 6、mechanics 1・vehicle_screw |
| 完成艇 | 2x2、船体4・seat1・paddle1・cargo1、エンジンなし | `raft`: 2x2、boat_board4・seat4・hand_paddles1。`canoe`: 1x4、boat_board4・seat2・hand_paddles1 |

- 本modは「序盤の都市廃材で組める」代わりに、耐久・出力・修理効率を下げる。バニラの上位艇を置き換えない。速度の上限比較は `canoe` を基準にする（`raft` は seat 4個で重く、単純比較に適さない）。

### テスト手順
1. `bash scripts/validate.sh mods/medium/scrap_boat` でJSON構文チェック（Level1）
2. `bash scripts/place_mod_for_test.sh --dry-run mods/medium/scrap_boat` で既存配置を確認→ `--force` で配置
3. `bash scripts/check_mods.sh --isolated --check-errors scrap_boat` でmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - 専用3種・6個をクラフト
   - `constr_veh` で2x2のフレームを組み、`seat` と専用部品を装着
   - 水辺で浮上、パドル移動、カーゴ積載、脱着、修理を確認
   - セーブ/ロード後も車両と積載が保持されることを確認
- 確認は fab 1・mechanics 1 の技能条件を満たすキャラで行い、深水・平水（流れなし）、無積載→満載（`sb_cargo` 定格30 L相当）の順に浮上を確認する（Step 6実装後に実行）

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし、`--check-errors` 付き）
- [ ] Level3: 組立・浮上・パドル移動・積載・脱着・修理・セーブ/ロード確認（手動。Level定義の正本は `rules/verification.md`）
- [ ] Step 9: 移動速度が `canoe` 以下（同一キャラ・無積載・平水で比較）、船体耐久（JSON値）が `raft_board` 以下、深水の対岸へ渡河可能、比較表と一致
- [ ] `design.md` が実装値と一致

### リスク
- 2x2・船体4個でdraftがsealed heightを超え、沈む可能性。Level3で確認し、必要なら船体数を増やすか `sb_hull_item` の重量を下げる。
- 560 Wのパドルが遅すぎる場合、600 Wまで調整する（`hand_paddles` 720 W以下を維持）。
- カーゴ30 Lが過大な場合、25 Lに下げる（`basketsm` 20 Lとの差を維持）。
- `FLOATS` の挙動は0.I/0.Jで変更される可能性がある。Level2/3で再確認する。

### ID衝突確認記録
- `sb_` 接頭辞: `external/cdda/data/json/` と `mods/` に既存IDなし。
- `scrap_boat`: mod ID・ディレクトリ名ともに未使用。
- `raft_board` / `hand_paddles` / `basketsm_abstract` / `bike_basket` はバニラ定義を参照するのみで、IDの再定義はしない。
