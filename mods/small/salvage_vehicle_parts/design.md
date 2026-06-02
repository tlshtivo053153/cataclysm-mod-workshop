## Mod設計書: salvage_vehicle_parts

### 仕様書から継承
- **目的**: CDDA 0.I RC 向けに、即席・低コストで設置できる車両改造パーツ5種を追加する。溶接不要で序盤〜中盤の車両カスタマイズを可能にする。
- **スコープ**:
  - **含むもの**: 即席 vehicle_part 5種、ITEM (TOOL) 5件、レシピ 5件（CSC_OTHER_VEHICLE カテゴリ）
  - **含まないもの**: モンスタードロップ・シナリオ・職業・変異・CBM、バッテリー・エンジン・電装系、ライト系、既存アイテム/既存 vehicle_part の改変
- **成功基準**:
  - 5種すべてがスポーン・クラフト・設置・機能する
  - 即席シート: 搭乗可能、シートベルト装着可
  - バスケット: アイテム格納可
  - ベッド: 睡眠時に「bed」選択肢
  - ワークベンチ: 「craft here」が使用可
  - クラクション: コントロールから honk 選択肢
  - 起動エラーなし

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| vehicle_part | `svp_improv_seat` | 即席シート（SEAT+BOARDABLE+BELTABLE） |
| vehicle_part | `svp_basket_rack` | 即席リアバスケット（CARGO+BOARDABLE） |
| vehicle_part | `svp_improv_bed` | 即席ベッド（BED+BOARDABLE+NONBELTABLE） |
| vehicle_part | `svp_makeshift_workbench` | 即席ワークベンチ（WORKBENCH+FLAT_SURF+CARGO+OBSTACLE） |
| vehicle_part | `svp_claxon_horn` | 即席クラクション（HORN） |
| ITEM (TOOL) | `svp_improv_seat_item` | 設置用アイテム |
| ITEM (TOOL) | `svp_basket_rack_item` | 〃 |
| ITEM (TOOL) | `svp_improv_bed_item` | 〃 |
| ITEM (TOOL) | `svp_makeshift_workbench_item` | 〃 |
| ITEM (TOOL) | `svp_claxon_horn_item` | 〃 |
| recipe | `svp_improv_seat` 他5件 | クラフトレシピ（result は ITEM ID） |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/vehicleparts/vp_flags.json` — 使用フラグ存在確認（SEAT, BOARDABLE, BELTABLE, CARGO, BED, NONBELTABLE, WORKBENCH, FLAT_SURF, OBSTACLE, HORN）
- [x] `external/cdda/data/json/vehicleparts/seats.json` — `seat` 雛形（flags, comfort, durability, requirements）
- [x] `external/cdda/data/json/vehicleparts/vehicle_parts.json` — `bed`, `horn_bicycle/car/big`, `veh_table`, `veh_table_foldable`
- [x] `external/cdda/data/json/vehicleparts/cargo.json` — `basketlg_folding`（CARGO 雛形）
- [x] `external/cdda/data/json/items/vehicle/seating.json` — TOOL 雛形
- [x] `external/cdda/data/json/recipes/recipe_vehicle.json` — `CSC_OTHER_VEHICLE` レシピ雛形
- [x] requirement ID — `vehicle_screw`, `vehicle_wrench_2`, `adhesive`, `sewing_standard`
- [x] quality ID — `HAMMER`, `SAW_W`
- [x] component ID — `2x4`, `nail`, `cotton_patchwork`, `sheet_cotton`, `nuts_bolts`, `basket`, `wire`, `sheet_cotton`, `blanket`, `sleeping_bag`, `wood_panel`, `sheet_metal_small`, `horn_bicycle`, `battery`

### ファイル構成
```
mods/small/salvage_vehicle_parts/
├── modinfo.json
├── design.md
└── data/
    ├── items.json          # 5件の TOOL 定義（svp_*_item）
    ├── vehicle_parts.json  # 5件の vehicle_part 定義（svp_*）
    └── recipes.json        # 5件のレシピ（result は svp_*_item）
```

### 実装順序
1. modinfo.json
2. data/items.json
3. data/vehicle_parts.json
4. data/recipes.json

### データフロー
```
recipe.result  →  ITEM (TOOL)         →  vehicle_part.item
     ↑                  ↑                          ↑
  クラフトで生成      設置時に消費             車両に装着して機能
```

### 設計上の特徴
- **溶接不要**: 全 part の requirements.install は `vehicle_screw` または `vehicle_wrench_2` のみ。即席コンセプト維持
- **低スキル**: install は mechanics/fabrication スキル 0〜1、difficulty 1〜2
- **低耐久**: バニラの同種 part の 1/3〜1/2 程度（durability 30〜120）
- **低活動量**: 全レシピ `LIGHT_EXERCISE` または `MODERATE_EXERCISE`
- **name 形式**: TOOL subtype は `{"str": "..."}` 形式（version_diff ルール準拠）
- **データフロー整合**: recipe.result と vehicle_part.item は `<ID>_item` で対応

### テスト手順
1. `bash scripts/validate.sh mods/small/salvage_vehicle_parts` でJSON構文OK（Level1）
2. `bash scripts/link_mod_for_test.sh mods/small/salvage_vehicle_parts` でCDDAに配置
3. `bash scripts/check_mods.sh` でmod読み込みエラーなし（Level2）
4. CDDA 0.I RC で起動して Level3 確認:
   - デバッグメニューで各 ITEM（`svp_*_item`）をスポーン
   - 各 ITEM からレシピでクラフト → ITEM が手に入る
   - 近接車両に各 part をインストール → 想定フラグが UI に反映

### 完了条件
- [x] Level1: JSON構文OK
- [ ] Level2: 起動OK（mod有効化時エラーなし）
- [ ] Level3: 5種すべてがスポーン・クラフト・設置・機能する
- [x] `design.md` を `templates/design_template.md` 準拠で作成
- [ ] 起動後、特有エラー（フラグ未定義・recipe の activity_level 欠落・recipe result と ITEM ID 不一致 等）がない
