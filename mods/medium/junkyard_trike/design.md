## Mod設計書: Junkyard Trike（廃材トライク）

### 仕様書から継承
- **目的**: `junkcycle` は2輪バイク向けの部品mod。本modは3輪の荷運び車を組むための専用パーツキットを追加し、序盤〜中盤の輸送を成立させる。専用2種は低スキル・無溶接で作れるが耐久は低い。車体のバニラ部品は既存の溶接・工具要件をそのまま使う。
- **スコープ**:
  - 含むもの: 専用 vehicle_part 2種＋設置ITEM 2点＋レシピ 2点。車体はバニラ流用（`frame_wood` / `xlframe`、`wheel_mount_light[_steerable]`、`wheel_bicycle` / `wheel_motorbike`、`saddle`、`controls`、`engine_1cyl`、`tank_small`、`battery_motorbike_small`、`alternator_motorbike`、`muffler`）。
  - 含まないもの: 新車両システム、完成車 `type: "vehicle"` プロトタイプ、`vehicle_group` 注入、トレーラー連結、装甲車、電気版、武器、サイドカー、前面ガード、既存車両の改変。
- **成功基準**: 専用2種をクラフトし、バニラフレームに装着して3輪車を組める。総積載65 L、最高速 `motorcycle_3wheel` 以下。Level1/2通過、Level3で組立・積載・走行・給油・脱着・修理・セーブ/ロード確認。

### ターゲットバージョン
- CDDA: 0.I RC（確認checkout: `f044a1c7c4f6184c129ce6dacff99ea573df326a`。計画書の `46730b6` と異なるため本設計のgrep結果を正とする）

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | copy-from | 説明 |
|---|---|---|---|
| vehicle_part | `jt_cargo_bed` | `basketlg_external`（50 L）を主参照 | 大型荷台。`size` 50 L |
| vehicle_part | `jt_side_basket` | `basketsm_external`（15 L）を参照 | 側面バスケット。`size` 15 L |
| ITEM | `jt_cargo_bed_item` | `basket`（ITEM 22.5 L・6 kg／対応part 50 L級） | 設置アイテム。`weight`・`volume` は軽量化上書き、`COOK` 1・`melee_damage` は引き継がない |
| ITEM | `jt_side_basket_item` | `bike_basket`（1.2 kg・5 L） | 設置アイテム |
| recipe | `jt_cargo_bed_item` | —（`result` が識別子） | 1件 |
| recipe | `jt_side_basket_item` | —（同上） | 1件 |

命名規約: 全IDは `jt_` 接頭辞。`recipe.result` は ITEM ID、vehicle_part.item も同じ ITEM ID。0.I の通常レシピに `id` フィールドは付けない。

### リンク
- `jt_cargo_bed.item` = `jt_cargo_bed_item`
- `jt_side_basket.item` = `jt_side_basket_item`
- 各レシピの `result` は対応するITEM ID。

### vehicle_partの必須項目
| 項目 | `jt_cargo_bed` | `jt_side_basket` |
|---|---|---|
| `name` / `copy-from` / `item` / `location` | 必須。`location` は親継承の `structure` | 同左 |
| `durability` | 目標40（親75より低い。ドラフト、Level3で確定） | 同左 |
| `requirements`（install / removal / repair） | 親は `welding_standard` 系。**専用2種のみ無溶接方針と矛盾するため明示的に上書き**し、`vehicle_nail_install` / `vehicle_screw` / `adhesive` 等で溶接工具を要求しない | 同左 |
| `flags` | 親の4つ（`UNMOUNT_ON_DAMAGE` / `CARGO` / `PROTRUSION` / `CARGO_PASSABLE`）をすべて継承（残す） | 同左 |
| `breaks_into` | 親に定義なし。`scrap` / `lc_wire` 中心に新規定義（ドラフト） | 同左 |
| CARGO固有 `size` | 50 L | 15 L。合計65 L |

車体のバニラ部品（`wheel_mount_light` / `controls` / `muffler` / `xlframe` 等）は既存の溶接要件を維持する。完成車全体の無溶接を主張しない。

### 3輪レイアウト
- フレーム3枚: 前1・後2。
- 前輪: `wheel_mount_light_steerable` + `wheel_bicycle` / `wheel_motorbike`。
- 後輪: `wheel_mount_light` ×2 + 車輪。
- 荷台・側面バスケットを後部フレームに装着する。

### バニラ流用パーツ（manifest）
- フレーム: `frame_wood` / `xlframe`
- 車輪: `wheel_mount_light_steerable`、`wheel_mount_light`、`wheel_bicycle` / `wheel_motorbike`
- 運転: `saddle`、`controls`
- 動力: `engine_1cyl`、`tank_small`（fuel: gasoline）、`battery_motorbike_small`、`alternator_motorbike`、`muffler`

### レシピ必須項目
| 項目 | 2レシピ共通の決定 |
|---|---|
| `result` | 対応するITEM ID |
| `category` / `subcategory` | `CC_OTHER` / `CSC_OTHER_VEHICLE` |
| `activity_level` | `LIGHT_EXERCISE`（ドラフト） |
| `autolearn` | `true` |
| `tools` / `using` | 溶接工具なし（`vehicle_screw` / `adhesive` 系）。install側も同様 |
| `skill_used` / `difficulty` / `time` | mechanics 1 / 1 / 30 m（ドラフト、Level3で確定） |
| `components` / `qualities` | 無溶接・低スキル方針で実装時に確定 |

### 比較対象
- `motorcycle_3wheel`（3輪）、`quad_bike`（4輪）、`junkcycle`（既存の2輪部品mod）、`basketlg_external`（50 L）、`basketsm_external`（15 L）。
- 総積載65 L、最高速 `motorcycle_3wheel` 以下、専用2種は無溶接・低耐久。`junkcycle` の `jk_cargo`（20 L）との差別化を明記する（本modは荷台50 L＋側面15 Lの3輪輸送特化）。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/vehicleparts/cargo.json` — `basketlg_external`（50 L / durability 75 / install `welding_standard` 60＋mechanics 1、`item: basket`、`location: structure`）、`basketsm_external`（15 L / durability 75 / install `welding_standard` 20、`item: bike_basket`）。両者とも `breaks_into` なし、`flags: UNMOUNT_ON_DAMAGE / CARGO / PROTRUSION / CARGO_PASSABLE`
- [x] `external/cdda/data/json/vehicleparts/frames.json` — `frame_wood`
- [x] `external/cdda/data/json/vehicleparts/wheel.json` — `wheel_mount_light` / `wheel_mount_light_steerable`
- [x] `external/cdda/data/json/vehicleparts/combustion.json` — `engine_1cyl`
- [x] `external/cdda/data/json/vehicleparts/tanks.json` — `tank_small`
- [x] `external/cdda/data/json/requirements/vehicle.json` — `vehicle_nail_install` / `vehicle_screw` 実在
- [x] `external/cdda/data/json/requirements/toolsets.json` — `welding_standard` 実在（親要件の確認用。上書きで排除する）
- [x] `external/cdda/data/json/recipes/recipe_vehicle.json` — `CSC_OTHER_VEHICLE` 実在、`activity_level` 実在
- [x] `external/cdda/data/json/vehicles/bikes.json` — `motorcycle_3wheel` / `quad_bike`（比較対象）
- [x] `external/cdda/data/json/items/vehicle/cargo.json` — `basket` / `bike_basket`（ITEM親）
- [x] `external/cdda/data/json/materials.json` — `lc_steel`（設置ITEM親 `basket` の素材）等の実在確認
- [x] `mods/medium/junkcycle/` — 既存パーツ（`jk_*`）との差別化確認。新規ID `jt_*` との衝突なし
- 備考: 新規フラグを追加しないため `vp_flags.json` の確認は不要（すべて親から継承）

### ファイル構成
```
mods/medium/junkyard_trike/
├── modinfo.json
├── spec.md
├── design.md
└── data/
    ├── items.json          # ITEM 2点
    ├── vehicle_parts.json  # vehicle_part 2点
    └── recipes.json        # recipe 2点
```

### 実装順序
1. modinfo.json
2. data/items.json
3. data/vehicle_parts.json
4. data/recipes.json
- 各編集後に Level1。逸脱はその都度 design.md に反映。

### テスト手順
1. `bash scripts/validate.sh mods/medium/junkyard_trike` でJSON構文チェック（Level1）
2. `bash scripts/place_mod_for_test.sh --dry-run mods/medium/junkyard_trike` で既存配置を確認→`--force` で配置
3. `bash scripts/check_mods.sh --isolated --check-errors junkyard_trike` でmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認: デバッグスポーン／組立／積載／走行／給油／脱着／修理／セーブロード

### 完了条件
- [ ] Level1: JSON構文OK（未実行、本設計は未実装）
- [ ] Level2: 起動OK（未実行、本設計は未実装）
- [ ] Level3: 組立・走行・脱着・修理確認（未実行、本設計は未実装）
- [ ] Step 9: 最高速・耐久・コストの比較（Level3未確認の間はバランス確定をしない）
- [ ] `design.md` が実装値と一致（実装時に更新）

### リスク
- パーツの `item` リンク切れ（`recipe.result` と `vehicle_part.item` の不一致）。
- 無溶接requirementsの上書き漏れ（親の `welding_standard` が残ると方針矛盾）。
- `junkcycle` との役割重複（本modは3輪・65 L輸送特化で差別化）。
- 3輪レイアウトの組立ミス、満載時の速度不足。Level3まで未確認の間はバランス確定をしない。

### ID衝突確認記録
- 新規ID（`jt_*` 6件）は `external/cdda/data/json` と `mods/` に存在せず、衝突なし（`jk_*` とも重ならない）。
- JSON実装は行わない。`modinfo.json` / `data/*.json` は未作成。Level1/2/3未実行。
