## Mod設計書: Junkcycle（廃材バイク）

### 仕様書から継承
- **目的**: 序盤に「廃材部品で移動手段を組む」体験を追加する。専用部品3種は低スキルで作れるが、完成にはバニラ駆動部品の溶接・mechanics 2が必要。既存 vehicle システムの拡張のみで、新ゲームシステムは追加しない。
- **スコープ**:
  - 含むもの: 専用 vehicle_part 3種＋設置 ITEM 3点＋レシピ 3点。バニラ流用（`frame_wood` ×3、`wheel_mount_light[_steerable]`、`tank_small`、`controls`、`engine_1cyl`、`battery_motorbike_small`、`alternator_motorbike`、`muffler`）。
  - 含まないもの: 新mapgen、NPC、モンスター、シナリオ、職業、専用フレーム/タンク、完成車プロトタイプ、電気版/装甲/武器/サイドカー/折りたたみ、既存車両・既存レシピの改変、完成車全体の無溶接化。
- **成功基準**: 専用3種・4個をクラフトし、`frame_wood` ×3 車両に装着して給油・走行。専用3種の製作・装着は低スキル、修理は溶接不要（ホイールのみ mechanics 2）。Level1/Level2 通過、Level3で組立・走行・脱着・修理・セーブ/ロード確認、最高速 `motorcycle_cross` 以下、耐久・コスト比較あり。

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | copy-from | 説明 |
|---|---|---|---|
| vehicle_part | `jk_wheel` | `wheel_bicycle` | 廃材ホイール。durability 30。install/removal/repair・フラグ・variants は親継承 |
| vehicle_part | `jk_saddle` | `saddle` | 廃材サドル。durability 40。install/removal は親継承、repair のみ上書き |
| vehicle_part | `jk_cargo` | `basketsm` | 簡易カーゴ。durability 40、容量20 L継承。install/removal は親継承、repair のみ上書き |
| ITEM | `jk_wheel_item` | `wheel_bicycle` | WHEEL subtype・diameter/width 継承 |
| ITEM | `jk_saddle_item` | `saddle` | `material` を leather/cotton に上書き |
| ITEM | `jk_cargo_item` | `bike_basket` | カーゴ設置アイテム |
| recipe | `jk_wheel_item` | — | `result` が識別子。1件 |
| recipe | `jk_saddle_item` | — | 同上。1件 |
| recipe | `jk_cargo_item` | — | 同上。1件 |

命名規約: 全IDは `jk_` 接頭辞。`recipe.result` は ITEM ID、vehicle_part.item も同じ ITEM ID。0.I の通常レシピに `id` フィールドは付けない。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/vehicleparts/wheel.json` — `wheel_bicycle`（durability 40、repair mechanics 2＋adhesive_rubber/tire_rubber、flags WHEEL/UNSTABLE_WHEEL/NEEDS_JACKING/NEEDS_WHEEL_MOUNT_LIGHT）、`wheel_mount_light[_steerable]`
- [x] `external/cdda/data/json/vehicleparts/seats.json` — `saddle`（durability 80、install mechanics 1＋vehicle_wrench_2、repair は溶接あり→上書き）、`seat`
- [x] `external/cdda/data/json/vehicleparts/cargo.json` — `basketsm_abstract`/`basketsm`（durability 75、size 20 L、install mechanics 1＋vehicle_screw、repair は溶接あり→上書き）
- [x] `external/cdda/data/json/items/vehicle/wheel.json` — `wheel_bicycle`（WHEEL subtype、diameter 27/width 3、material aluminum/rubber）
- [x] `external/cdda/data/json/items/vehicle/seating.json` — `saddle`（copy-from seat、weight 300 g、volume 1250 ml）、`seat`
- [x] `external/cdda/data/json/items/vehicle/cargo.json` — `bike_basket`（copy-from basket、weight 1200 g、volume 5 L）、`basket`
- [x] `external/cdda/data/json/vehicleparts/tanks.json` — `tank_small`（item jerrycan、容量10 L、install drilling_standard 20）
- [x] `external/cdda/data/json/vehicleparts/vehicle_parts.json` — `controls`（溶接120＋vehicle_bolt_install 2）、`muffler`（溶接80＋vehicle_bolt_install 1）
- [x] `external/cdda/data/json/vehicleparts/combustion.json` — `engine_1cyl`（mechanics 2＋WRENCH 2）
- [x] `external/cdda/data/json/vehicleparts/battery.json` — `battery_motorbike_small`
- [x] `external/cdda/data/json/vehicleparts/alternator.json` — `alternator_motorbike`（install mechanics 2＋vehicle_screw）
- [x] `external/cdda/data/json/items/vehicle/frames.json` — `frame_wood`
- [x] `external/cdda/data/json/vehicleparts/frames.json` — `frame_wood` part 側（参考）
- [x] `external/cdda/data/json/vehicles/bikes.json` — `motorcycle_cross`（比較対象。engine_1cyl_large 使用）
- [x] `external/cdda/data/json/requirements/vehicle.json` — `vehicle_wrench_2`、`vehicle_screw`、`vehicle_bolt_install` 実在
- [x] `external/cdda/data/json/requirements/toolsets.json` — `welding_standard`、`sewing_standard`、`adhesive`、`adhesive_rubber`、`tire_rubber`、`cutting_wire_standard`、`drilling_standard` 実在
- [x] `external/cdda/data/json/recipes/recipe_vehicle.json` — `CSC_OTHER_VEHICLE` 雛形、activity_level（LIGHT/MODERATE_EXERCISE）実在、`basket`/`bike_basket`（lc_wire 使用例）、`frame_wood`（2x4＋nail）実在
- [x] `external/cdda/data/json/materials.json` — `leather`、`cotton`、`steel`、`rubber`、`wood` 実在
- [x] `external/cdda/data/json/tool_qualities.json` — `HAMMER`、`CUT`、`WRENCH` 実在
- [x] `external/cdda/data/json/items/generic.json` — `lc_wire` 実在（本modでは `lc_wire` を使用。バニラ現行レシピ・lootに合わせる）
- [x] 新規フラグなし（すべて親から継承）

### ファイル構成
```
mods/medium/junkcycle/
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
jk_wheel_item → jk_wheel_item → jk_wheel
jk_saddle_item → jk_saddle_item → jk_saddle
jk_cargo_item → jk_cargo_item → jk_cargo
```

### ITEM 詳細
- `jk_wheel_item`（copy-from `wheel_bicycle`）: name `scrap wheel`、material `[steel, rubber]`、price `15 USD` / postapoc `50 cent`。weight/volume/diameter/width は親継承（1500 g / 11 L / 27 / 3）。WHEEL subtype 継承。
- `jk_saddle_item`（copy-from `saddle`）: name `scrap saddle`、material `[leather, cotton]`、price `10 USD` / postapoc `50 cent`。weight/volume は親継承（300 g / 1250 ml）。
- `jk_cargo_item`（copy-from `bike_basket`）: name `scrap cargo basket`、material `[steel]`、price `15 USD` / postapoc `50 cent`。weight/volume は親継承（1200 g / 5 L）。

### vehicle_part 詳細
- `jk_wheel`: copy-from `wheel_bicycle`、durability 30（親40より低い）。requirements・flags・variants は継承（install/removal `vehicle_wrench_2`、repair `adhesive_rubber`＋`tire_rubber` mechanics 2、溶接なし）。breaks_into のみ上書き（`mc_steel` を出さない）: scrap / lc_wire / chunk_rubber / rubber_tire_chunk（すべて `count`）。
- `jk_saddle`: copy-from `saddle`、durability 40（親80より低い）。install/removal・flags・variants は継承（`vehicle_wrench_2`）。repair のみ上書き: skills fabrication 1、time 15 m、using sewing_standard 4＋adhesive 1（溶接なし）。breaks_into 上書き: leather / cotton_patchwork / scrap（すべて `count`）。
- `jk_cargo`: copy-from `basketsm`、durability 40（親75より低い）、size 20 L・flags・variants継承。install/removal は継承（`vehicle_screw`）。repair のみ上書き: skills fabrication 1、time 15 m、using adhesive 1（溶接なし）。breaks_into 新規: lc_wire / scrap（すべて `count`、親に breaks_into なし）。

### レシピ詳細
共通: `category CC_OTHER`、`subcategory CSC_OTHER_VEHICLE`、`autolearn true`、`activity_level` 必須。
- `jk_wheel_item`: fab 1、25 m、MODERATE_EXERCISE、qualities HAMMER 1、using cutting_wire_standard 1。components: chunk_rubber×2 または rubber_tire_chunk×4、scrap×2、lc_wire×4、nuts_bolts×4。
- `jk_saddle_item`: fab 1、20 m、LIGHT_EXERCISE、qualities CUT 1＋HAMMER 1。components: leather×2 または cotton_patchwork×4、scrap×1、nail×4。
- `jk_cargo_item`: fab 1、15 m、LIGHT_EXERCISE、qualities HAMMER 1、using cutting_wire_standard 1。components: lc_wire×10、scrap×2、pipe×1。

### バニラ流用と全体要件（Level3 前提）
| 部品 | 個数 | 装着要件 |
|---|---|---|
| `frame_wood` | 3 | fabrication 1、HAMMER 2、nail 20/枚 |
| `wheel_mount_light_steerable`（前） | 1 | mechanics 2、溶接25 |
| `wheel_mount_light`（後） | 1 | mechanics 2、溶接25 |
| `jk_wheel` | 2 | WRENCH 2 |
| `jk_saddle` | 1 | WRENCH 2 |
| `tank_small` | 1 | mechanics 1、WRENCH 1、drilling_standard 20 |
| `jk_cargo` | 1 | SCREW 1 |
| `controls` | 1 | mechanics 2、溶接120、vehicle_bolt_install 2回 |
| `engine_1cyl` | 1 | mechanics 2、WRENCH 2 |
| `battery_motorbike_small` | 1 | WRENCH 1 |
| `alternator_motorbike` | 1 | mechanics 2、SCREW 1（engineと同タイル） |
| `muffler` | 1 | mechanics 2、溶接80、vehicle_bolt_install 1回 |

設置合計: 溶接250 cm、nails 60、nuts_bolts 60。レイアウトは 1x3（x=1 前輪、x=0 中央、x=-1 後輪）。装着順は frame → mount → wheel。前マウントは必ず steerable。完成車プロトタイプは追加しない。

### テスト手順
1. `bash scripts/validate.sh mods/medium/junkcycle` でJSON構文チェック（Level1）
2. `bash scripts/place_mod_for_test.sh --dry-run mods/medium/junkcycle` で既存配置を確認→ `--force` で配置
3. `bash scripts/check_mods.sh --isolated --check-errors junkcycle` でmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認（手順は計画書 §9 参照。手動）

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし、`--check-errors` 付き）
- [ ] Level3: フル組み立て・走行・給油・専用3種の脱着/修理・セーブ/ロード確認（手動）
- [ ] Step 9: 実測最高速が `motorcycle_cross` 以下、耐久・コストの比較表あり
- [ ] `design.md` が実装値と一致
