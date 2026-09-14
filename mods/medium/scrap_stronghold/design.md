## Mod設計書: Scrap Stronghold（廃材拠点クラフト）

### 仕様書から継承
- **目的**: 溶接機なしで拠点を固められる廃材中心の低コスト建築（construction＋furniture）を追加し、序盤の拠点防衛と食料自給の足がかりを提供する。
- **スコープ**: 含む→廃材バリケード（constr1＋家具1）・廃材プランター（constr1＋家具6連鎖）・廃材収納クレート（constr1＋家具1）・construction_group1件。含まない→モンスター・NPC・シナリオ・職業・mapgen・魔法・BIONIC・車両・trap、既存データの改変、雨水収集機能。
- **成功基準**: 建築メニューから建設可能、Level1・Level2通過、バニラ比「安いが弱い」（耐久50〜70%、釘ゼロ〜半減・板材半減、分解回収渋化）。本タスクはLevel2まで。Level3未実行（残留リスクはspec.md参照）。

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| construction_group | `scsh_build_scrap` | 建築メニュー表示グループ「Build Scrap Structures」 |
| construction | `scsh_constr_scrap_barricade` | 廃材バリケード建設（fab1・HAMMER1・20分） |
| furniture | `f_scsh_barricade` | 廃材バリケード本体（coverage20・bash3〜24） |
| construction | `scsh_constr_scrap_planter` | 廃材プランター建設（fab2・HAMMER2＋SAW_W1・25分） |
| furniture | `f_scsh_planter` | 廃材プランター本体（base。PLANTABLE＋dirtmound） |
| furniture | `f_scsh_planter_seed` | 生育段階：種 |
| furniture | `f_scsh_planter_seedling` | 生育段階：発芽 |
| furniture | `f_scsh_planter_mature` | 生育段階：成長 |
| furniture | `f_scsh_planter_harvest` | 生育段階：収穫可 |
| furniture | `f_scsh_planter_overgrown` | 生育段階：枯死 |
| construction | `scsh_constr_scrap_crate` | 廃材クレート建設（fab0・HAMMER1＋SAW_W1・30分） |
| furniture | `f_scsh_crate` | 廃材クレート本体（coverage40・SHORT収納） |

- 設計判断：construction 3件とプランター家具6段階は `copy-from` 不使用の完全手書き定義とする
  （バニラconstructionに継承前例なし、plant_data継承はバニラ連鎖に吸収されるため）。
  家具IDは全て `f_` 始まり（`f_scsh_*`）とする。エンジンが `post_terrain` の `f_` 接頭辞で
  furniture判定するため、`scsh_` 始まりは `invalid terrain id` エラーになる（Level2で実証済み）。
  バリケード家具・クレート家具の2件のみ `copy-from`＋差分上書きとする
  （継承元が単体家具で連鎖吸収の恐れがなく、手書きのフィールド欠落リスクを避けるため）。
  - `f_scsh_barricade`：`copy-from: f_barricade_road`。上書き＝name・description・symbol・bgcolor・coverage(20)・required_str(4)・bash・deconstruct（他は継承：flags・move_cost_mod・examine_action: chainfence等）。
  - `f_scsh_crate`：`copy-from: f_crate_o`。上書き＝name・description・symbol・bgcolor・coverage(40)・required_str(8)・bash・deconstruct（他は継承：flags 8件・move_cost_mod等）。
  - プランター6段階：全手書き。flags・connect_groups・connects_to・examine_action・move_cost_mod・required_strはバニラ対応段階と同一値を持たせる（下表の通り）。
  - プランター6段階の `plant_data.transform` / `base`・bash内 `furn_set` は全て `scsh_` 張替え。

### プランター生育連鎖対応表
| 自ID | 元ID | transform | base | examine_action | 備考 |
|---|---|---|---|---|---|
| `f_scsh_planter` | `f_planter` | `f_scsh_planter_seed` | —（base自体） | `dirtmound` | PLANTABLE＋FLAT＋MOUNTABLE＋TRANSPARENT、connect PLANTER |
| `f_scsh_planter_seed` | `f_planter_seed` | `f_scsh_planter_seedling` | `f_scsh_planter` | `aggie_plant` | バニラ段階と同一flags |
| `f_scsh_planter_seedling` | `f_planter_seedling` | `f_scsh_planter_mature` | `f_scsh_planter` | `aggie_plant` | GROWTH_SEEDLING継承相当 |
| `f_scsh_planter_mature` | `f_planter_mature` | `f_scsh_planter_harvest` | `f_scsh_planter` | `aggie_plant` | GROWTH_MATURE継承相当 |
| `f_scsh_planter_harvest` | `f_planter_harvest` | `f_scsh_planter_overgrown` | `f_scsh_planter` | `harvest_plant_ex` | GROWTH_HARVEST継承相当 |
| `f_scsh_planter_overgrown` | `f_planter_unharvested_overgrown` | `f_scsh_planter_overgrown`（自己） | `f_scsh_planter` | `clear_overgrown` | GROWTH_OVERGROWN継承相当 |

### construction定義明細
- `scsh_constr_scrap_barricade`：group `scsh_build_scrap`、category `OTHER`（元OTHER踏襲）、
  required_skills [[fabrication, 1]]、time `"20 m"`、activity_level `MODERATE_EXERCISE`、
  qualities [[{id: HAMMER, level: 1}]]、components [[[2x4, 3]]・[[scrap, 4]]・[[wire, 2]]・[[nails, 6, LIST]]]、
  pre_special `check_empty`、post_terrain `f_scsh_barricade`。
- `scsh_constr_scrap_planter`：group `scsh_build_scrap`、category `FURN`（元FURN踏襲）、
  required_skills [[fabrication, 2]]、time `"25 m"`、activity_level `MODERATE_EXERCISE`、
  qualities [[{id: HAMMER, level: 2}]・[{id: SAW_W, level: 1}]]、
  components [[[2x4, 6]]・[[nails, 18, LIST]]・[[pebble, 100]]・[[material_soil, 75]]]、
  pre_special `check_empty`、post_terrain `f_scsh_planter`。
- `scsh_constr_scrap_crate`：group `scsh_build_scrap`、category `FURN`（元FURN踏襲）、
  required_skills [[fabrication, 0]]、time `"30 m"`、activity_level `LIGHT_EXERCISE`、
  qualities [[{id: HAMMER, level: 1}]・[{id: SAW_W, level: 1}]]、
  components [[[2x4, 4]]・[[scrap, 2]]・[[nails, 12, LIST]]]、
  pre_special `check_empty`、post_terrain `f_scsh_crate`。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/construction/furniture_barriers.json` — `constr_barricade_road`（fab1・HAMMER1・20分・2x4x6＋nails12・post f_barricade_road）
- [x] `external/cdda/data/json/construction/furniture_domestic_plants.json` — `constr_planter`（fab3・HAMMER2＋SAW_W2・25分・2x4x12＋nails36＋pebble200＋soil75）
- [x] `external/cdda/data/json/construction/furniture_storage.json` — `constr_crate_o`（fab1・45分・HAMMER2＋SAW_W2）
- [x] `external/cdda/data/json/construction/windows.json` — `constr_window_boarded`（B1対抗馬）
- [x] `external/cdda/data/json/construction_group.json` — `build_road_barricade` / `build_planter`（形式確認。新規groupは同形式で定義）
- [x] `external/cdda/data/json/construction_category.json` — `OTHER` / `FURN` カテゴリ実在
- [x] `external/cdda/data/json/furniture_and_terrain/furniture-barriers.json` — `f_barricade_road`（coverage30・bash3〜40・chainfence）
- [x] `external/cdda/data/json/furniture_and_terrain/furniture-domestic_plants.json` — `f_planter` 系6段階（plant_data連鎖・examine各種・PLANTER接続）
- [x] `external/cdda/data/json/furniture_and_terrain/furniture-storage.json` — `f_crate_o`（coverage60・bash12〜40・SHORT）
- [x] `external/cdda/data/json/requirements/materials.json` — `nails` LIST（nail/bronze_nail）実在
- [x] `external/cdda/data/json/items/` — `scrap` / `wire` / `2x4` / `material_soil` / `pebble` / `splinter` / `withered` / `leaves` / `twig` 実在
- [x] `external/cdda/doc/JSON/JSON_INFO.md` — Constructions節（group・category・required_skills・qualities・activity_level・time・components・pre_special・post_terrain）
- [x] `mods/small/heavy_crowbar/modinfo.json` — modinfo.json形式

### ファイル構成
- modinfo.json（id: `scrap_stronghold`、category: `items`、dependencies: dda）
- data/construction_groups.json（scsh_build_scrap 1件）
- data/constructions.json（3件）
- data/furniture.json（8件：バリケード1＋プランター系6＋クレート1）
- 合計ID：group1＋constr3＋家具8＝12件

### 実装順序
1. modinfo.json
2. data/construction_groups.json
3. data/constructions.json
4. data/furniture.json

### テスト手順
1. validate.shでJSON構文チェック（Level1。編集のたび）
2. place_mod_for_test.shでCDDAに配置
3. check_mods.sh --isolated --check-errorsでmod読み込み確認（Level2）＋debug.logのERROR確認
4. Level3（CDDA起動・建築・生育・分解の手動確認）は**本タスクでは未実行**。実行前の本番利用・バランス確定は禁止。

### 完了条件（2026-09-14 時点）
- [x] Level1: JSON構文OK（`bash scripts/validate.sh` 全ファイル通過）
- [x] Level2: 起動OK（`check_mods.sh --isolated --check-errors` 通過、debug.log ERRORゼロ）
- [ ] Level3: **未実行**（本タスクのスコープ外。以下は未検証の残留リスク）
  - プランター生育全段階の `f_scsh_*` 連鎖遷移・収穫後の自作 base 復帰
  - bash耐久・分解回収内容が設計通りであること
  - バリケードの移動阻止・建築メニュー表示
  - 上記未検証のため、バランス確定・本番利用は Level3 実行後に行うこと
