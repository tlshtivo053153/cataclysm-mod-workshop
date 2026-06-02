# vehicle_part 実装パターン

CDDAに新規車両パーツ（vehicle_part）を追加するためのパターンファイル。

## 概要

vehicle_part は **3要素** の組み合わせを基本とし、**recipe.result は ITEM ID**（vehicle_part ID ではない）という点に注意。

- **ITEM (TOOL) 定義** (`"type": "ITEM"`, `"subtypes": ["TOOL"]`): プレイヤーが所持・設置するアイテム。vehicle_part の `item` フィールドから参照される
- **vehicle_part 定義** (`"type": "vehicle_part"`): 車両に装着して機能する部品。`item` フィールドで ITEM ID を参照
- **recipe 定義** (`"type": "recipe"`): ITEM を生成するクラフトレシピ。`result` は ITEM ID

recipe は雛形 mod でも必須（craft による入手経路を保証するため）。item_group 経由のみで配布する場合は省略可だが、新規 mod では recipe 雛形を推奨。

## ファイル構成

小規模 vehicle_part mod（5 part＋5 item＋5 recipe）の最小構成：

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "vehicles"` 推奨 |
| `data/items.json` | `ITEM` (TOOL) | 設置用パーツアイテム ×N（`category: "veh_parts"`） |
| `data/vehicle_parts.json` | `vehicle_part` | 車両パーツ定義 ×N |
| `data/recipes.json` | `recipe` | 製作レシピ ×N（`result` は ITEM ID） |

## データフロー（最重要）

```
recipe.result  →  ITEM (TOOL)         →  vehicle_part.item
     ↑                  ↑                          ↑
  クラフトで生成      設置時に消費             車両に装着して機能
```

- `recipe.result` は **必ず ITEM ID**（`<id>_item` 形式）。vehicle_part ID ではない
- `vehicle_part.item` も **必ず ITEM ID**。recipe.result と一致させる
- 命名規則 `<vehicle_part_id>_item` で機械的にチェック可能

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/vehicleparts/vp_flags.json` | 全 vehicle_part フラグ定義。**使用フラグの実在確認に必須** |
| `data/json/vehicleparts/seats.json` | SEAT 系 part 雛形（`seat`, `reclining_seat`, `seat_back`, `saddle`） |
| `data/json/vehicleparts/vehicle_parts.json` | `bed`, `horn_bicycle/car/big`, `veh_table`, `workbench` 等の雛形 |
| `data/json/vehicleparts/cargo.json` | CARGO 系 part 雛形（`basketlg`, `cargo_bag`, `basketlg_folding` 等） |
| `data/json/items/vehicle/seating.json` | シート系 ITEM (TOOL) 雛形（`seat`, `saddle`, `folding_seat`） |
| `data/json/items/vehicle/cargo.json` | CARGO 系 ITEM 雛形（`basket`, `bike_basket`, `bike_rack`） |
| `data/json/items/tool/misc.json` | `horn_bicycle` 等のノイズ系 TOOL 雛形 |
| `data/json/recipes/recipe_vehicle.json` | `CSC_OTHER_VEHICLE` レシピ雛形 |
| `data/json/requirements/vehicle.json` | `vehicle_screw`, `vehicle_wrench_1/2`, `vehicle_weld_removal`, `vehicle_nail_install` |
| `data/json/requirements/toolsets.json` | `welding_standard`, `sewing_standard`, `surface_heat` 等の汎用 requirement |

## 必須フラグの実在確認

`vp_flags.json` で必ず実在確認すること。**フラグが存在しない（または名称変更済み）**と起動時にエラー。

### 0.I RC で実在確認済みフラグ（小規模 mod で頻出）

| フラグ | 用途 | 雛形 part | 補足 |
|---|---|---|---|
| `SEAT` | 搭乗可能 | `seat` | `BOARDABLE` と併用 |
| `BOARDABLE` | 搭乗可（SEAT と同時に指定） | `seat` | |
| `BELTABLE` | シートベルト装着可 | `seat` | `NONBELTABLE` と排他 |
| `NONBELTABLE` | シートベルト不可 | `bed` | `BELTABLE` と排他 |
| `CARGO` | アイテム格納 | `basketlg`, `bed` | `size` フィールド指定に必須 |
| `BED` | 睡眠可 | `bed` | `comfort`, `floor_bedding_warmth` と併用 |
| `WORKBENCH` | クラフト可 | `veh_table` | **part 側に `workbench: { multiplier, mass, volume }` 必須** |
| `FLAT_SURF` | 平らな作業面 | `veh_table`, `cargo_bag` | `WORKBENCH` と併用可 |
| `OBSTACLE` | 障害物（キャラクタが衝突） | `veh_table` | |
| `HORN` | クラクション | `horn_bicycle` | **ITEM 側に TOOL + `manualnoise` use_action 必須**。part 側に `bonus` で音量制御 |
| `CARGO_PASSABLE` | 中を通れるカーゴ | `cargo_bag` | |

### 削除・要電源フラグ（避けること）

| フラグ | 理由 |
|---|---|
| `FENDER` | **0.I で削除済み**。mud flap 系は実装不可 |
| `CONE_LIGHT`, `CIRCLE_LIGHT`, `HEADLIGHT` 等 | `ENABLED_DRAINS_EPOWER` + `epower` 必須。即席コンセプトに合わず |
| `STEREO`, `CHIMES`, `FRIDGE` 等 | バッテリー + epower 必須 |

## 雛形（IMPROV シート：SALVAGE コンセプト）

### 1. ITEM (TOOL) 定義

```json
{
  "type": "ITEM",
  "id": "svp_improv_seat_item",
  "name": { "str": "makeshift padded seat" },
  "description": "A salvaged seat assembled from wooden boards, padding cut from old clothing, and a handful of bolts.",
  "weight": "5000 g",
  "color": "brown",
  "symbol": "0",
  "material": [ "wood", "cotton" ],
  "volume": "5000 ml",
  "category": "veh_parts",
  "price": "50 cent",
  "price_postapoc": "10 cent",
  "melee_damage": { "bash": 4 }
}
```

### 2. vehicle_part 定義

```json
{
  "type": "vehicle_part",
  "id": "svp_improv_seat",
  "name": { "str": "makeshift padded seat" },
  "looks_like": "seat",
  "categories": [ "operations", "passengers" ],
  "color": "brown",
  "broken_color": "brown",
  "damage_modifier": 75,
  "damage_reduction": { "all": 1, "bash": 3 },
  "comfort": 1,
  "floor_bedding_warmth": 50,
  "description": "A seat cobbled together from wooden boards and salvaged padding.",
  "durability": 120,
  "flags": [ "SEAT", "BOARDABLE", "BELTABLE" ],
  "item": "svp_improv_seat_item",
  "location": "center",
  "requirements": {
    "install": { "skills": [ [ "mechanics", 1 ] ], "time": "15 m", "using": [ [ "vehicle_wrench_2", 1 ] ] },
    "removal": { "skills": [ [ "mechanics", 1 ] ], "time": "10 m", "using": [ [ "vehicle_wrench_2", 1 ] ] },
    "repair": { "skills": [ [ "mechanics", 1 ] ], "time": "15 m", "using": [ [ "adhesive", 1 ], [ "sewing_standard", 4 ] ] }
  },
  "breaks_into": "ig_vp_seat",
  "variants": [ { "symbols": "#", "symbols_broken": "*" } ]
}
```

### 3. recipe 定義

```json
{
  "type": "recipe",
  "activity_level": "LIGHT_EXERCISE",
  "result": "svp_improv_seat_item",
  "category": "CC_OTHER",
  "subcategory": "CSC_OTHER_VEHICLE",
  "skill_used": "fabrication",
  "difficulty": 1,
  "time": "20 m",
  "autolearn": true,
  "qualities": [ { "id": "HAMMER", "level": 1 }, { "id": "SAW_W", "level": 1 } ],
  "components": [
    [ [ "2x4", 4 ] ],
    [ [ "nail", 8 ] ],
    [ [ "cotton_patchwork", 4 ], [ "sheet_cotton", 3 ] ],
    [ [ "nuts_bolts", 4 ] ]
  ]
}
```

### 4. HORN フラグ雛形（TOOL + manualnoise 必須）

HORN フラグ付き part は **ITEM 側も TOOL subtype + `manualnoise` use_action** を持つ必要がある。これがないと車両コントロールから honk しても音が鳴らない。

```json
{
  "type": "ITEM",
  "subtypes": [ "TOOL" ],
  "id": "svp_claxon_horn_item",
  "name": { "str": "makeshift claxon horn" },
  "description": "An old bulb horn wired to a single battery.",
  "weight": "400 g",
  "volume": "750 ml",
  "category": "veh_parts",
  "material": [ "plastic", "aluminum" ],
  "use_action": {
    "type": "manualnoise",
    "moves": 100,
    "noise": 18,
    "noise_message": "HONK!",
    "noise_id": "misc",
    "noise_variant": "horn_bicycle",
    "use_message": "You squeeze the bulb."
  }
}
```

```json
{
  "type": "vehicle_part",
  "id": "svp_claxon_horn",
  "name": { "str": "makeshift claxon horn" },
  "looks_like": "horn_bicycle",
  "item": "svp_claxon_horn_item",
  "bonus": 30,
  "durability": 30,
  "flags": [ "HORN" ],
  "requirements": {
    "install": { "skills": [ [ "mechanics", 0 ] ], "time": "5 m", "using": [ [ "vehicle_screw", 1 ] ] },
    "removal": { "skills": [ [ "mechanics", 0 ] ], "time": "5 m", "using": [ [ "vehicle_screw", 1 ] ] }
  },
  "variants": [ { "symbols": "*", "symbols_broken": "*" } ]
}
```

- `bonus` フィールドで音量制御（バニラ `horn_bicycle: 45`, `horn_car: 100`, `horn_big: 120`）
- `noise` 値は use_action 側で設定（part 側とは別）

### 5. WORKBENCH フラグ雛形（part 側に workbench フィールド必須）

`WORKBENCH` フラグ付き part は **part 側に `workbench` オブジェクト**が必要。これがないと「craft here」メニューが機能しない。

```json
{
  "type": "vehicle_part",
  "id": "svp_makeshift_workbench",
  "name": { "str": "makeshift vehicle workbench" },
  "looks_like": "veh_table",
  "item": "svp_makeshift_workbench_item",
  "durability": 80,
  "flags": [ "WORKBENCH", "FLAT_SURF", "CARGO", "OBSTACLE" ],
  "workbench": { "multiplier": 1.05, "mass": 100000, "volume": "15 L" },
  "requirements": {
    "install": { "skills": [ [ "fabrication", 1 ] ], "time": "15 m", "using": [ [ "vehicle_wrench_2", 1 ] ] }
  }
}
```

- `multiplier`: クラフト速度倍率（1.0 = 等倍、1.5 = 1.5倍速）
- `mass`: クラフト可能なアイテムの最大重量（グラム）
- `volume`: クラフト可能なアイテムの最大体積

## 設計ガイドライン（即席・サルベージ系）

- **溶接不要**: `requirements.install` は `vehicle_screw` または `vehicle_wrench_2` のみ。即席コンセプト維持
- **低スキル**: install は mechanics/fabrication 0〜1、difficulty 1〜2
- **低耐久**: バニラの同種 part の 1/3〜1/2 程度（durability 30〜120）
- **低活動量**: レシピは `LIGHT_EXERCISE` または `MODERATE_EXERCISE`（0.I 必須）
- **ITEM name 形式**: `{"str": "..."}` を使用（`str_sp` ではない。`{"str_sp": "..."}` は ITEM でも不可）
- **データフロー整合**: recipe.result と vehicle_part.item は `<vehicle_part_id>_item` で対応
- **`location` フィールド**: 主要値は以下の通り
  - `"center"`: 標準的な中央スロット（seat, bed, cargo 等）
  - `"structure"`: フレーム強化用（handle, trunk 等）
  - `"anywhere"`: 任意のスロット（bike_rack, foldable 等）
  - `"on_roof"`: 屋根上のみ
  - `"on_cargo"` / `"on_seat"`: カーゴ上/シート上のみ
  - **省略可**: 多くの場合 `"center"` 相当のデフォルト位置が使われる（vehicle_part 雛形による）

## よくあるエラー（vehicle_part 固有）

| エラー | 原因 | 解決策 |
|---|---|---|
| `vehicle part X is not CARGO and cannot define size` | `size` フィールドがあるが CARGO フラグなし | CARGO フラグを付けるか `size` を削除 |
| `Invalid or misplaced field name "ammo"` (TOOL アイテム) | TOOL subtype で `ammo` フィールドを定義 | `ammo` フィールドは AMMO subtype でのみ有効。TOOL では削除 |
| `itemgroup entry for spawning item X defined charges but can't have any` | `breaks_into` のエントリで charge 非対応アイテムに `charges` を指定 | `count` に変更。charge 非対応は GENERIC ITEM（subtype 未定義）で、AMMO/TOOL 対応 (`max_charges` 設定済) は対応 |
| `unrecognized vehicle part flag "FENDER"` | 0.I で削除済みフラグを使用 | フラグを削除 or 別フラグに置換 |
| HORN を実装してもクラクションが鳴らない | ITEM 側に TOOL + `manualnoise` use_action がない | `"subtypes": ["TOOL"]` 追加し、`use_action: { "type": "manualnoise", ... }` を定義 |
| WORKBENCH を実装してもクラフトできない | part 側に `workbench` フィールドがない | `workbench: { "multiplier": 1.0〜1.5, "mass": 100000〜200000, "volume": "10 L〜30 L" }` を追加 |

## 命名規則の例

| 種別 | ID パターン | 例 |
|---|---|---|
| vehicle_part | `<mod_prefix>_<descriptor>` | `svp_improv_seat` |
| ITEM (TOOL) | `<vehicle_part_id>_item` | `svp_improv_seat_item` |
| recipe | `<vehicle_part_id>` | `svp_improv_seat` |

命名規則を守ることで、`vehicle_part_id + "_item"` で機械的に ITEM ID を導出でき、データフロー整合性のチェックが容易になる。**この `_item` サフィックス規則は本フレームワーク mod 内のローカル規約**であり、CDDA 自体は同名（例: `seat` part が `seat` ITEM を参照）でも動作する。バニラ互換の vehicle_part を拡張する mod ではバニラ命名（`_item` なし）に揃えること。

## 参考: 既存実装例

- `mods/small/salvage_vehicle_parts/` — 5 part すべてを vehicle_part で実装した小規模 mod の実例

## 関連ドキュメント

- [`rules/CORE.md`](../CORE.md) — Step 4「CDDA 参照との整合性確認」の手順（本ファイルで参照する vp_flags.json 確認の基礎）
- [`rules/verification.md`](../verification.md) — Level1/2/3 テスト手順（実装後の検証フロー）
- [`rules/version_diff.md`](../version_diff.md) — 0.I での vehicle_part 関連変更（`FENDER` 削除、`rag` 統合）
- [`rules/common_errors.md`](../common_errors.md) — vehicle_part 固有のエラー詳細（エラー集）
