## Mod設計書: fortified_shelters

### 目的
CDDAの避難シェルターに「防衛強化型」のバリエーションを2種類追加する。バリケード・武器庫・監視所などの防御的要素を備えた避難所で、既存シナリオ（Evacuee, Squatter, Sheltered）からスタート地点として選択可能にする。

### スコープ
- **含む:**
  - 新規シェルターmapgen: Style D「Fortified Garage」（ガレージ改装型、1階+屋根+地下）、Style E「Watchtower Shelter」（監視塔型、1階+屋根監視デッキ+地下）
  - スタート地点2種: `sloc_fortified_garage`, `sloc_fortified_watchtower`
  - 既存シナリオ3種の拡張（`evacuee`, `squatter`, `alone`）
  - overmap_terrain 6種 + overmap_special 2種（ワールド自動生成用）
  - 専用パレット `fortified_shelter`
- **含まない:**
  - 新規シナリオ、新規アイテム、新規モンスター、新規NPC、新規アイテムグループ

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 成功基準
- Level1: JSON構文エラーなし
- Level2: CDDA起動時にmod読み込みエラーなし（--check-mods exit 0）
- Level3: デバッグメニューから新シェルターを開始地点として選択可能、マップが正しく生成される

### 使用ID一覧

| 種別 | ID | 説明 |
|---|---|---|
| MOD_INFO | `fortified_shelters` | mod識別子 |
| palette | `fortified_shelter` | 防衛型シェルター用パレット（`shelter`継承） |
| overmap_terrain | `shelter_d` | Style D ガレージ地上階（`shelter_abstract`継承） |
| overmap_terrain | `shelter_d_roof` | Style D ガレージ屋根 |
| overmap_terrain | `shelter_d_under` | Style D ガレージ地下室 |
| overmap_terrain | `shelter_e` | Style E 監視塔地上階（`shelter_abstract`継承） |
| overmap_terrain | `shelter_e_roof` | Style E 監視塔屋根（監視デッキ） |
| overmap_terrain | `shelter_e_under` | Style E 監視塔地下室 |
| mapgen | `shelter_d` | Style D 地上階 mapgen（24x24） |
| mapgen | `shelter_d_roof` | Style D 屋根 mapgen（24x24） |
| mapgen | `shelter_d_under` | Style D 地下室 mapgen（24x24） |
| mapgen | `shelter_e` | Style E 地上階 mapgen（24x24） |
| mapgen | `shelter_e_roof` | Style E 屋根監視デッキ mapgen（24x24） |
| mapgen | `shelter_e_under` | Style E 地下室 mapgen（24x24） |
| start_location | `sloc_fortified_garage` | ガレージシェルター開始地点 |
| start_location | `sloc_fortified_watchtower` | 監視塔シェルター開始地点 |
| overmap_special | `Fortified Garage Shelter` | Style D ワールド自動生成（3層 `_north` 回転対応） |
| overmap_special | `Fortified Watchtower Shelter` | Style E ワールド自動生成（3層 `_north` 回転対応） |

### 拡張した既存シナリオ

| 拡張元 scenario | 追加する sloc | 備考 |
|---|---|---|
| `evacuee` (Evacuee) | `sloc_fortified_garage`, `sloc_fortified_watchtower` | `copy-from` + `extend` で `allowed_locs` に追加 |
| `squatter` (Squatter) | 同上 | |
| `alone` (Sheltered) | 同上 | |

### Style D: Fortified Garage 設計仕様

**コンセプト**: 自動車整備工場を改装した防御拠点。東西に細長いレイアウト（20x14建物、24x24グリッド中央）。

| 要素 | 使用ID | mapgen文字 |
|---|---|---|
| 外周壁 | parametrized_walls（`#`） | `#` |
| メイン入口（南側） | `t_door_metal_c`（金属ドア両開き） | `=` |
| 土嚢バリケード（室内外周） | `f_sandbag_half` | `~` |
| 板張り窓（北・東） | `t_window_boarded` | `{` |
| 鉄格子窓 | `t_window_bars` | `}` |
| 作業台 | `f_workbench` | `w` |
| 重機械 | `f_machinery_heavy` | `M` |
| 電子ガンセーフ | `f_gun_safe_el`（item: `army_personal_locker`） | `G` |
| 木箱（弾薬庫） | `f_crate_c`（item: `milspec_arsenal_only_guns_or_ammo`） | `8` |
| アームチェア | `f_armchair` | `H` |
| ソファ | `f_sofa` | `F` |
| 薪ストーブ | `f_woodstove` | `W` |
| 流し台 | `f_sink`（継承） | `S` |
| ロッカー | `f_locker`（継承） | `l` |
| 食器棚 | `f_cupboard`（継承） | `c` |
| 下り階段 | `t_stairs_down`（継承） | `>` |
| 屋根梯子 | `t_ladder_up`（継承） | `*` |

**屋根**: `t_flat_roof` 平坦屋根 + 砂嚢監視ポスト（`f_sandbag_half`）、梯子でアクセス。

**地下室**: 弾薬クレート（`f_crate_c`）、ラック（`f_rack`）、ロッカー、トイレ、階段上り口。

### Style E: Watchtower Shelter 設計仕様

**コンセプト**: 2階建て監視塔を備えたコンパクトな正方形レイアウト（12x12建物、24x24グリッド中心）。

| 要素 | 使用ID | mapgen文字 |
|---|---|---|
| 外壁 | parametrized_walls（`#`） | `#` |
| 鉄格子窓（全周） | `t_window_bars` | `}` |
| 金属ドア入口 | `t_door_metal_c` | `=` |
| 通信コンソール | `f_console` | `K` |
| 机 | `f_desk` | `D` |
| 電子ガンセーフ | `f_gun_safe_el`（item: `army_personal_locker`） | `G` |
| 木箱（弾薬庫） | `f_crate_c`（item: `milspec_arsenal_only_guns_or_ammo`） | `8` |
| ベッド | `f_bed` | `a` |
| 薪ストーブ | `f_woodstove` | `W` |
| 流し台・ゴミ箱・食器棚 | `f_sink`, `f_trashcan`, `f_cupboard`（継承） | `S`, `%`, `c` |
| 下り階段 | `t_stairs_down`（継承） | `>` |
| 屋根梯子 | `t_ladder_up`（継承） | `*` |

**屋根**: 監視デッキ — `t_railing`（手すり）で囲まれた `t_flat_roof` + `f_sandbag_half`（砂嚢）。`roof_palette` 継承 + インライン地形/家具定義で上書き。

**地下室**: 標準シェルター地下室同様の備蓄（ロッカー `f_locker`、ユーティリティ棚 `f_utility_shelf`、トイレ、流し台）。

### パレット仕様

`fortified_shelter` パレットは `shelter` パレット（さらに `parametrized_walls_palette` を継承）を継承。以下のマッピングを追加:

**terrain（上書き/追加）:**
| 文字 | 地形ID | 用途 |
|---|---|---|
| `{` | `t_window_boarded` | 板張り窓 |
| `}` | `t_window_bars` | 鉄格子窓 |
| `=` | `t_door_metal_c` | 金属ドア |
| `3` | `t_door_metal_locked` | 施錠金属ドア（未使用、予備） |
| `@` | `t_railing` | 手すり |

**furniture（追加）:**
| 文字 | 家具ID | 用途 |
|---|---|---|
| `~` | `f_sandbag_half` | 半壁土嚢 |
| `w` | `f_workbench` | 作業台 |
| `G` | `f_gun_safe_el` | 電子ガンセーフ |
| `M` | `f_machinery_heavy` | 重機械 |
| `H` | `f_armchair` | アームチェア |
| `F` | `f_sofa` | ソファ |
| `W` | `f_woodstove` | 薪ストーブ |
| `a` | `f_bed` | ベッド |
| `D` | `f_desk` | 机 |
| `K` | `f_console` | 通信コンソール |
| `Y` | `f_rack` | ラック |
| `8` | `f_crate_c` | 閉じた木箱 |
| `9` | `f_filing_cabinet` | 書類キャビネット |

**items（追加）:**
| 文字 | アイテムグループ | chance |
|---|---|---|
| `G` | `army_personal_locker` | 80 |
| `8` | `milspec_arsenal_only_guns_or_ammo` | 70 |
| `Y` | `SUS_evac_shelter_supply_closet` | 60 |
| `9` | `SUS_evac_shelter_supply_closet` | 60 |

### 特記事項

- **`_north` 命名規則**: overmap_special では OMT 名に `_north` を付与（回転対応）するが、mapgen の `om_terrain` フィールドにはサフィックスなしのIDを記述する。
- **`roof_palette` の文字競合**: `~` は `roof_palette` で `f_chimney`（煙突）にマップされるため、屋根mapgenではインライン `furniture` 定義で `f_sandbag_half` に上書きしている。`*` は `roof_palette` に定義がないため、インライン `terrain` 定義で `t_ladder_up` に追加している。
- **mapgen `rows` の文字制限**: `,`（カンマ）はCDDA mapgenで特殊な意味を持つ可能性があるため、全mapgen行で `.`（ドット）に置換済み。未マップ文字は `fill_ter` が適用される。
- **overmap_terrain**: 全6種とも `copy-from: shelter_abstract` で `sym: "+"`, `color: "white"`, `vision_levels: "isolated_building"`, `see_cost: "high"` を継承。地上階には `KNOWN_DOWN`, `SOURCE_PEOPLE`, `SOURCE_SAFETY` フラグを付与。
- **`f_gun_safe_el`**: バニラに存在する電子式ガンセーフ。単純なメカニカル金庫 `f_gun_safe` はCDDAに存在しない。
- **`place_zones`**: 各地上階 mapgen で `ZONE_START_POINT` + `faction: your_followers` を定義（NPCフォロワー開始地点）。

### 参照ファイル（external/cdda/） — 実在確認済み

- [x] `data/json/mapgen/shelter.json` — 既存シェルターmapgenパターン・`place_zones`記法
- [x] `data/json/mapgen_palettes/shelter.json` — 全シェルター用パレット（`shelter`, `shelter_used`, `shelter_vandal`, `shelter_survivor`, `shelter_unfinished`, `shelter_infested`）
- [x] `data/json/mapgen_palettes/common_parameters.json` — `parametrized_walls_palette` 定義
- [x] `data/json/mapgen_palettes/roof_palette.json` — 屋根用パレット（`roof_palette`）の文字マッピング
- [x] `data/json/overmap/overmap_terrain/overmap_terrain_military.json` — `shelter_abstract`（:70）、全シェルター系om_terrain
- [x] `data/json/overmap/overmap_special/specials.json` — `Evac Shelter` special（:1582）の3層 `_north` パターン
- [x] `data/json/scenarios.json` — `evacuee`(:4), `squatter`(:47), `alone`(:659) の拡張元確認
- [x] `data/json/start_locations.json` — 既存 sloc_ 定義のフォーマット確認
- [x] `data/json/itemgroups/military.json` — `army_personal_locker`（:578）実在確認
- [x] `data/json/itemgroups/Weapons_Mods_Ammo/arsenal/collections.json` — `milspec_arsenal_only_guns_or_ammo`（:138）実在確認
- [x] `data/json/itemgroups/SUS/evac_shelter.json` — `SUS_evac_shelter_*` シリーズ実在確認

### ファイル構成

```
mods/small/fortified_shelters/
├── modinfo.json
├── design.md
├── data/
│   ├── start_locations.json
│   ├── scenario_extensions.json
│   ├── mapgen/
│   │   ├── fortified_garage.json
│   │   └── fortified_watchtower.json
│   ├── palette/
│   │   └── fortified_shelter.json
│   └── overmap/
│       ├── overmap_terrain.json
│       └── overmap_special.json
```

### 実装順序
1. modinfo.json
2. overmap_terrain.json
3. palette/fortified_shelter.json
4. mapgen/fortified_garage.json（地上階→屋根→地下室）
5. mapgen/fortified_watchtower.json（地上階→屋根→地下室）
6. start_locations.json
7. scenario_extensions.json
8. overmap_special.json

### テスト手順
1. `bash scripts/validate.sh mods/small/fortified_shelters` でJSON構文チェック（Level1）
2. `bash scripts/link_mod_for_test.sh mods/small/fortified_shelters` でCDDAにシンボリックリンク
3. `bash scripts/check_mods.sh fortified_shelters` でmod読み込み確認（Level2）
4. CDDAを起動 → 新規ゲーム → Evacuee/Squatter/Shelteredシナリオで「Fortified Garage Shelter」「Watchtower Shelter」が開始地点として選択可能であること
5. デバッグメニューでマップ生成を確認（Level3）

### 完了条件
- [x] Level1: JSON構文OK（全8ファイル）
- [x] Level2: 起動OK（`--check-mods` exit 0、JSONエラーなし）
- [ ] Level3: 意図通り動作（ゲーム内確認）
  - [ ] Evacueeシナリオで `sloc_fortified_garage` が開始地点として選択可能
  - [ ] Evacueeシナリオで `sloc_fortified_watchtower` が開始地点として選択可能
  - [ ] Squatterシナリオで両開始地点が選択可能
  - [ ] Shelteredシナリオで両開始地点が選択可能
  - [ ] Style D（Fortified Garage）のマップが正しく生成される
  - [ ] Style E（Watchtower Shelter）のマップが正しく生成される
  - [ ] 各mapgenの `ZONE_START_POINT` が正しく機能する
