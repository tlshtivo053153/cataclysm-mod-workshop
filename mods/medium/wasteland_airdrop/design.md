## Mod設計書: Wasteland Airdrop（廃土の救難投下）

### 仕様書から継承
- **目的**: プレイヤーが電子工作で救難ビーコンを作り、30分後に予約地点へ供給投下を呼ぶ。投下地点には物資とゾンビが発生し、リスクとリターンのある能動的な補給ループを作る。
- **スコープ**:
  - 含むもの: 救難ビーコン3種（医療／生活／軍用）、各レシピ3件、起動EOC 3件、共通投下EOC 1件、投下mapgen update 3件。既存の `airdrop_*` item group を再利用。
  - 含まないもの: 新規モンスター、NPC、シナリオ、職業、車両、魔法、BIONIC、新規mapgen拠点・overmap special、既存アイテム・既存レシピ・既存airdropの改変、投下物資の完全保証。
- **成功基準**: 3種をクラフト・使用でき、屋外で30分後に予約地点へ投下。パラシュート・パレット・物資・ゾンビが配置される。屋内拒否、二重予約拒否、セーブ／ロード後の投下維持を確認。Level1/2/3を通過し、ビーコン費用と投下物資・ゾンビリスクが見合う。

### ターゲットバージョン
- CDDA: 0.I RC（確認checkout: `47c9bf9e183ba3d13044e10de3af73bb9e6b3158`。`external/cdda` の git HEAD。`VERSION.txt` のビルド元 `46730b6` とは異なるため、本設計のgrep結果を正とする）

### 依存関係
- 依存mod: dda（必須）

### modinfo.json
| 項目 | 値 |
|---|---|
| type | `MOD_INFO` |
| id | `wasteland_airdrop` |
| name | `Wasteland Airdrop` |
| authors | `[ "cdda_mod_framework" ]` |
| description | `Craft signal beacons to call supply drops. The signal attracts the dead.` |
| category | `items` |
| dependencies | `[ "dda" ]` |
| version | `1.0` |

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| ITEM/TOOL | `wad_beacon_medical` | 医療用救難ビーコン。IFAK・水・MRE系を呼ぶ |
| ITEM/TOOL | `wad_beacon_supply` | 生活物資用救難ビーコン。人道支援投下を呼ぶ |
| ITEM/TOOL | `wad_beacon_military` | 軍用救難ビーコン。軍用キット・レア物資を呼ぶ |
| recipe | `wad_beacon_medical` | 医療用ビーコンのレシピ |
| recipe | `wad_beacon_supply` | 生活用ビーコンのレシピ |
| recipe | `wad_beacon_military` | 軍用ビーコンのレシピ |
| effect_on_condition | `wad_activate_medical` | 医療用ビーコン起動EOC |
| effect_on_condition | `wad_activate_supply` | 生活用ビーコン起動EOC |
| effect_on_condition | `wad_activate_military` | 軍用ビーコン起動EOC |
| effect_on_condition | `wad_drop` | 30分後の共通投下EOC |
| mapgen (update_mapgen_id) | `wad_airdrop_medical` | 医療投下の3x3 mapgen update |
| mapgen (update_mapgen_id) | `wad_airdrop_supply` | 生活投下の3x3 mapgen update |
| mapgen (update_mapgen_id) | `wad_airdrop_military` | 軍用投下の3x3 mapgen update |

- 新規IDは13件。`wad_` 接頭辞で統一。`#` 不使用、英小文字・数字・アンダースコアのみ。
- 既存の `airdrop_humanitarian_full` / `airdrop_humanitarian_looted` / `airdrop_trash` / `airdrop_military_kit` / `airdrop_IFAK` / `airdrop_MRE` / `airdrop_water_canteen` / `airdrop_water_drum` / `airdrop_generator` を再利用する。新規item_groupは作らない。
- 新規モンスター・monstergroupは作らない。`GROUP_ZOMBIE` をそのまま使う。

### グローバル変数
| 変数名 | 用途 | 初期値 |
|---|---|---|
| `g_wad_drop_type` | 投下種別（0=なし、1=医療、2=生活、3=軍用。0以外は予約中） | 0 |
| `g_wad_drop_loc` | 予約地点（`u_location_variable` で保存） | 未定義 |

- ワールドスコープの `global_val` を使う。キャラクター死亡・切り替えで投下予約が消えないようにするため。
- 同時予約は1件のみ。`g_wad_drop_type != 0` で排他制御する（予約フラグは `drop_type` に統合し別変数は持たない）。
- 変数名の `g_` は名前の一部。math `g_wad_drop_loc` と `{ "global_val": "g_wad_drop_loc" }` を同一名で書く。

### データフロー
```
ITEM use_action (effect_on_conditions)
  -> wad_activate_medical / supply / military
     -> g_wad_drop_type != 0 なら拒否メッセージ（予約中かつ屋内なら予約中を優先）
     -> u_is_outside でなければ拒否メッセージ
     -> u_consume_item でビーコン消費
     -> u_location_variable で g_wad_drop_loc に地点保存
     -> g_wad_drop_type = 1/2/3
     -> run_eocs "wad_drop" with time_in_future "30 minutes"
wad_drop (global: true)
  -> g_wad_drop_type == 1: mapgen_update "wad_airdrop_medical" at g_wad_drop_loc
  -> g_wad_drop_type == 2: mapgen_update "wad_airdrop_supply" at g_wad_drop_loc
  -> g_wad_drop_type == 3: mapgen_update "wad_airdrop_military" at g_wad_drop_loc
  -> 距離に応じたメッセージ
  -> g_wad_drop_type = 0
```

### ITEM 詳細
| 項目 | `wad_beacon_medical` | `wad_beacon_supply` | `wad_beacon_military` |
|---|---|---|---|
| name | `{ "str": "medical supply beacon" }` | `{ "str": "supply beacon" }` | `{ "str": "military supply beacon" }` |
| description | 医療用の救難トランスポンダ。信号は付近の死者を引き寄せる。 | 人道支援用の救難トランスポンダ。信号は付近の死者を引き寄せる。 | 軍用周波数に接続する救難トランスポンダ。信号は付近の死者を引き寄せる。 |
| weight / volume | 1200 g / 1500 ml | 1500 g / 2000 ml | 1800 g / 2500 ml |
| price / price_postapoc | `"40 USD"` / `"10 USD"` | `"50 USD"` / `"12 USD 50 cent"` | `"80 USD"` / `"20 USD"` |
| material | `[ "steel", "plastic", "aluminum" ]` | 同左 | `[ "steel", "aluminum", "plastic" ]` |
| symbol / color | `;` / `light_green` | `;` / `light_blue` | `;` / `green` |
| flags | `[ "WATER_BREAK", "ELECTRONIC" ]` | 同左 | 同左 |
| use_action | `effect_on_conditions` → `wad_activate_medical`、`menu_text: "Activate beacon"` | → `wad_activate_supply` | → `wad_activate_military` |

- ITEM（`"type": "ITEM"`, `"subtypes": ["TOOL"]`）の `name` は `{ "str": ... }` 形式（`str_sp` 不可）。
- `SINGLE_USE` は付けない。EOC の `u_consume_item` で消費する。二重消費を避けるため。
- ビーコンは1回限り。使用時に在庫から1個消費される。
- `use_action` の `menu_text` は既存の `fidget_spinner` 等と同じ形式。

### レシピ詳細
| 項目 | `wad_beacon_medical` | `wad_beacon_supply` | `wad_beacon_military` |
|---|---|---|---|
| result | `wad_beacon_medical` | `wad_beacon_supply` | `wad_beacon_military` |
| category / subcategory | `CC_ELECTRONIC` / `CSC_ELECTRONIC_TOOLS` | 同左 | 同左 |
| activity_level | `LIGHT_EXERCISE` | `LIGHT_EXERCISE` | `LIGHT_EXERCISE` |
| skill_used / difficulty | electronics 4 | electronics 5 | electronics 6 |
| time | 40 m | 1 h | 1 h 30 m |
| using | `soldering_standard` 10 | `soldering_standard` 12 | `soldering_standard` 16 |
| qualities | `SCREW` 1 | `SCREW` 1 | `SCREW` 1 |
| proficiencies | `prof_elec_soldering`, `prof_elec_circuits` | 同左＋`prof_elec_semiconductors` | 同左＋`prof_elec_semiconductors` |
| book_learn / autolearn | `autolearn: true` | `radio_book` 4, `textbook_electronics` 4（`book_learn: [[ "radio_book", 4 ], [ "textbook_electronics", 4 ]]` 形式） | `radio_book` 6, `textbook_electronics` 6（同形式） |

- components:
  - 医療: `two_way_radio` 1、`power_supply` 1、`e_scrap` 8、`scrap` 3、`cable` 6、`light_battery_cell` 1。
  - 生活: `two_way_radio` 1、`transponder` 1、`receiver` 1、`antenna` 1、`e_scrap` 10、`scrap` 4、`cable` 8、`light_battery_cell` 1。
  - 軍用: `two_way_radio` 1、`transponder` 1、`directional_antenna` 1、`power_supply` 1、`e_scrap` 12、`scrap` 6、`cable` 10、`medium_battery_cell` 1。
- 医療は `autolearn` で入り口を広くし、生活・軍用は書籍学習にする。軍用は `radio_book` 6 または `textbook_electronics` 6 を要求し、電子工作の上位目標にする。
- 既存の `two_way_radio` レシピ（electronics 4、30 m、`soldering_standard` 14）と比較し、ビーコンは追加部品と時間で一段上の投資にする。
- 既存の `hand_crank_charger` レシピ（electronics 3、30 m、`soldering_standard` 10）と比較し、医療ビーコンは同等〜やや上、軍用は明確に上。

### EOC 詳細
#### 起動EOC（3件共通構造）
- `wad_activate_medical` / `wad_activate_supply` / `wad_activate_military`。
- 条件分岐:
  1. `g_wad_drop_type != 0` → 「A drop is already inbound. Wait for the current signal to resolve.」を表示して終了。ビーコンは消費しない。
  2. `{ "not": "u_is_outside" }` → 「The beacon needs an open sky to transmit.」を表示して終了。ビーコンは消費しない。
  3. 成功 → 以下を順に実行。
     - `{ "u_consume_item": { "context_val": "id" } }` で対応ビーコンを1個消費（装備中でも消費できるようID直書きにしない）。
     - `u_location_variable` で `{ "global_val": "g_wad_drop_loc" }` に現在地を保存。
     - `g_wad_drop_type = 1/2/3`。
     - 「The beacon chirps and begins transmitting. Somewhere, a supply drop is being prepared.」を表示。
     - `run_eocs: "wad_drop"` を `time_in_future: "30 minutes"` で予約。
- 地点保存・フラグ設定は上記の順で書く。
- `u_message` の type は成功 `info`、拒否 `bad`。

#### 共通投下EOC `wad_drop`
- `"eoc_type": "ACTIVATION"`、`"global": true`（30分待ち中の死亡・キャラ切替でも発火し詰みを防ぐ）。
- ネストした `if` で `g_wad_drop_type` を判定し、対応する `mapgen_update` を `target_var: { "global_val": "g_wad_drop_loc" }` で実行（`switch` は値2でcase1+2が両方走る恐れがあるため使わない）。
  - 1 → `wad_airdrop_medical`
  - 2 → `wad_airdrop_supply`
  - 3 → `wad_airdrop_military`
- `distance('u', g_wad_drop_loc) <= 30` なら「A cargo parachute thumps down nearby. The signal has drawn attention.」、それ以外は「Somewhere in the distance, a supply drop lands.」を表示。
- 最後に `g_wad_drop_type = 0` に戻す。

### mapgen update 詳細
| 項目 | `wad_airdrop_medical` | `wad_airdrop_supply` | `wad_airdrop_military` |
|---|---|---|---|
| mapgensize | `[3, 3]` | `[3, 3]` | `[3, 3]` |
| center (1,1) item | `parachute_mil` 1 | `parachute_mil` 1 | `parachute_mil` 1 |
| center (1,1) furniture | `f_pallet_belted` | `f_pallet_belted` | `f_pallet_belted` |
| place_items | `airdrop_IFAK` 100%、`airdrop_water_canteen` 60%、`airdrop_MRE` 40% | `airdrop_humanitarian_looted` 100%、`airdrop_humanitarian_full` 25%、`airdrop_trash` 20% | `airdrop_military_kit` 100%、`airdrop_water_drum` 20%、`airdrop_generator` 5% |
| place_monster | `GROUP_ZOMBIE`、`"chance": 100`、`"repeat": [4, 6]` | 同、`"repeat": [6, 9]` | 同、`"repeat": [8, 12]` |
| monster x/y | `[0, 2]` / `[0, 2]` | 同左 | 同左 |
| terrain変更 | なし | なし | なし |

- `place_items` は複数エントリを同時に判定する。生活ビーコンはlootedが基本で、25%でfullが追加される。軍用はmilitary_kitが基本で、20%で水ドラム、5%で発電機が追加される。
- `airdrop_IFAK` / `airdrop_MRE` / `airdrop_water_canteen` は箱（`box_medium`）入りで生成される。`airdrop_humanitarian_*` は段ボール・テント・水を含む。
- `airdrop_generator` はディーゼル発電機・燃料・投光器を含むため、軍事ビーコンのみのレア枠とする。
- 地形は変更しない。既存の地面・道路・屋根の上に物資とパレットを置く。`ERASE_ALL_BEFORE_PLACING_TERRAIN` は使わない。
- 中央タイルに既存の家具がある場合、`f_pallet_belted` が上書きする可能性がある。投下地点として許容する。
- モンスターは投下地点の3x3内に配置される。プレイヤーが離れていても投下地点に湧く。

### バランス方針
- 既存の `mx_airdrop` は「full 5% / looted 93% / military 2%」のランダム。本modはビーコン費用とゾンビリスクの代償に、種別を選べる。
- 医療ビーコンはIFAK＋水＋MREで、序盤〜中盤の医療・水・食料を安定させる。費用は electronics 4 と `two_way_radio` 1個。
- 生活ビーコンはlooted基本＋25% full。費用は electronics 5 と `transponder` / `receiver` / `antenna`。
- 軍用ビーコンはmilitary_kit基本＋20%水ドラム＋5%発電機。費用は electronics 6 と `directional_antenna` / `medium_battery_cell`。
- ゾンビは医療4–6、生活6–9、軍用8–12。投下物資を回収するには戦闘または回避が必要。
- ビーコンは1回限り。投下物資にビーコン素材（`two_way_radio` / `transponder` / `directional_antenna`）は含まれないため、投下だけでは無限にビーコンを作れない。Level3で実際のドロップ内容を確認する。
- 同時予約1件の制限により、連打で大量投下できない。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/items/generic.json` — `transponder`、`antenna`、`power_supply`、`e_scrap`、`parachute_mil` 実在
- [x] `external/cdda/data/json/items/resources/metal.json` — `scrap`、`scrap_aluminum` 実在
- [x] `external/cdda/data/json/items/ammo.json` — `cable` 実在
- [x] `external/cdda/data/json/items/battery.json` — `light_battery_cell`、`medium_battery_cell` 実在
- [x] `external/cdda/data/json/items/tool/radio_tools.json` — `two_way_radio` 実在
- [x] `external/cdda/data/json/items/tool/electronics.json` — `directional_antenna`、`hand_crank_charger` 実在
- [x] `external/cdda/data/json/items/book/electronics.json` — `radio_book`（max_level 8）、`textbook_electronics`（max_level 6）実在
- [x] `external/cdda/data/json/itemgroups/Locations_MapExtras/airdrop.json` — `airdrop_humanitarian_full`、`airdrop_humanitarian_looted`、`airdrop_trash`、`airdrop_generator` 実在
- [x] `external/cdda/data/json/itemgroups/Locations_MapExtras/airdrop_mil.json` — `airdrop_military_kit`、`airdrop_IFAK`、`airdrop_MRE`、`airdrop_water_canteen`、`airdrop_water_drum` 実在
- [x] `external/cdda/data/json/furniture_and_terrain/furniture-storage.json` — `f_pallet_belted` 実在
- [x] `external/cdda/data/json/monstergroups/zombies.json` — `GROUP_ZOMBIE` 実在
- [x] `external/cdda/data/json/recipes/tools/tools_electronic.json` — `two_way_radio` レシピ（electronics 4、30 m、`LIGHT_EXERCISE`、`soldering_standard` 14、`SCREW` 1）
- [x] `external/cdda/data/json/recipes/other/parts.json` — `antenna`、`directional_antenna`、`transponder` レシピ
- [x] `external/cdda/data/json/recipes/other/power_supplies.json` — `hand_crank_charger` レシピ（electronics 3、30 m、`LIGHT_EXERCISE`、`soldering_standard` 10、`SCREW` 1）
- [x] `external/cdda/data/json/requirements/toolsets.json` — `soldering_standard` 実在
- [x] `external/cdda/data/json/tool_qualities.json` — `SCREW` 実在
- [x] `external/cdda/data/json/proficiencies/electronics.json` — `prof_elec_soldering`、`prof_elec_circuits`、`prof_elec_semiconductors` 実在
- [x] `external/cdda/doc/JSON/EFFECT_ON_CONDITION.md` — `u_location_variable`、`u_consume_item`、`mapgen_update` の `target_var` / `time_in_future`、`switch`、`math`、`distance()`
- [x] `external/cdda/data/json/effects_on_condition/vitrification_effect_on_condition.json` — `mapgen_update` + `target_var` の実例、`run_eocs` + `time_in_future` の実例
- [x] `external/cdda/data/json/effects_on_condition/portal_storm_effect_on_condition.json` — `time_in_future` に変数を使う実例、`distance('u', ...)` の実例
- [x] `external/cdda/data/json/effects_on_condition/mapgen_eocs/furniture_eocs.json` — `u_consume_item` の実例
- [x] `external/cdda/data/json/effects_on_condition/weather_eocs.json` — recurring EOC / `u_is_avatar` / `u_is_outside` の実例
- [x] `rules/patterns/eoc.md` — EOC の落とし穴（`u_is_avatar` の裸文字列、per-item EOC の最後の結果だけ残る問題 等）
- [x] `rules/CORE.md` — name形式、recipeの `activity_level` 必須、ID命名規則
- [x] `mods/small/scrap_striker/` / `mods/medium/scrap_hounds/` — 既存modのID命名・設計書スタイル確認
- [x] 新規ID `wad_*` 13件は `external/cdda/data/json` と `mods/` に存在せず、衝突なし（grep確認済み）

### ファイル構成
```
mods/medium/wasteland_airdrop/
├── modinfo.json
├── spec.md
├── design.md
└── data/
    ├── items.json          # ITEM/TOOL 3点
    ├── recipes.json        # recipe 3点
    ├── eoc.json            # effect_on_condition 4点
    └── mapgen_updates.json # mapgen update 3点
```

### 実装順序
1. `modinfo.json`
2. `data/items.json`（3アイテム）
3. `data/mapgen_updates.json`（3 mapgen update）
4. `data/eoc.json`（起動3＋共通投下1）
5. `data/recipes.json`（3レシピ）
- 各編集後に `bash scripts/validate.sh mods/medium/wasteland_airdrop`（Level1）。
- 実装中に設計から逸脱する場合は、その都度この設計書を更新する。

### テスト手順
1. `bash scripts/validate.sh mods/medium/wasteland_airdrop` でJSON構文チェック（Level1）。
2. `bash scripts/place_mod_for_test.sh --dry-run mods/medium/wasteland_airdrop` で既存配置を確認し、`--force` で配置。
3. `bash scripts/check_mods.sh --isolated --check-errors wasteland_airdrop` でmod読み込み確認（Level2）。`debug.log` の ERROR を確認。
4. CDDAを起動してLevel3確認:
   - デバッグメニューで3種のビーコンと素材をスポーン。
   - 各ビーコンをクラフトできること（デバッグのレシピ全開放は使わず、書籍なしでは生活・軍用が出ないこと、書籍で出ることを確認）。
   - 屋外で使用し、メッセージ・ビーコン消費・`g_wad_drop_type != 0` を確認。
   - デバッグで30分進め、予約地点にパラシュート・パレット・物資・ゾンビが出現すること（各typeで他種mapgenが混ざらないこと）。
   - 屋内で使用し、拒否メッセージ・ビーコン未消費・`g_wad_drop_type == 0` のまま・30分進めても何も起きないことを確認。
   - 予約中に別のビーコン・同種ビーコンを使い、拒否されること（予約中かつ屋内は予約中メッセージ優先）。
   - 予約直後にセーブ／ロードし、`g_wad_drop_type` が残っていること→30分進行→投下実行→`g_wad_drop_type == 0` を確認。ロード直後に消えたらrecurring EOC方式へ切替。
   - 予約後にその場を離れ、投下が予約地点に発生し、近傍／遠方の両メッセージを確認すること。
   - 3種のドロップ内容とゾンビ数を確認し、バランスを調整する（各3回ずつ投下し、投下物資に `two_way_radio` / `transponder` / `directional_antenna` が混ざらないこと。5%枠の率は検証せず出現有無のみ記録）。
   - 投下後に再度予約できること（リセット確認）。

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（ERRORなし、`--check-errors` 付き）
- [ ] Level3: 3種の投下・ゾンビ・ドロップ・屋内拒否・二重予約拒否（別種＋同種）・セーブ／ロード・投下後再予約・近傍／遠方メッセージを確認
- [ ] Step 9: ビーコン費用と投下物資・ゾンビリスクの比較を記録
- [ ] `design.md` が実装値と一致

### リスク
- 未定義のglobal変数 `g_wad_drop_type` の初期値。Level2で未定義時の挙動を確認し、必要ならmod読込時の初期化EOCを追加する。
- `run_eocs` + `time_in_future` がセーブ／ロードをまたいで保持されるか。保持されない場合、`g_wad_drop_time` に `time('now') + time('30 m')` を保存し、1分ごとのrecurring EOCで判定する方式に切り替える。
- `mapgen_update` + `target_var` が `global_val` の地点変数で正しく動くか。動かない場合、`map_spawn_item` で物資を地点に置き、`u_spawn_monster` でゾンビを湧かせる方式に切り替える（ゾンビはプレイヤー周辺になる制限付き）。
- `u_consume_item` がアイテム自身の `use_action` から呼んだ場合に在庫から消えるか。消えない場合、`SINGLE_USE` フラグまたは `u_remove_item_with` に切り替える。
- 投下地点が水・屋根・壁際の場合、物資の一部が消失・上書きされる可能性。屋外判定のみで許容する。
- 軍事ビーコンの `airdrop_generator` が強すぎる可能性。5%から開始し、Level3で調整する。
- ゾンビ数が多すぎる/少なすぎる可能性。医療4–6、生活6–9、軍用8–12から開始し、Level3で調整する。
- 同時予約1件の制限は意図的な簡略化。複数予約が必要になったら種別ごとのフラグに分割する（shortcut: 同時予約1件、複数予約が必要になったら種別ごとのフラグに分割）。

### ID衝突確認記録
- 新規ID（`wad_*` 13件）は `external/cdda/data/json` と `mods/` に存在せず、衝突なし。
- mod ID `wasteland_airdrop` も `mods/` に存在せず、衝突なし。
- `g_wad_drop_type` / `g_wad_drop_loc` はゲーム内IDではなくEOC変数。既存変数との衝突なし。
- JSON実装は行わない。`modinfo.json` / `data/*.json` は未作成。Level1/2/3未実行。
