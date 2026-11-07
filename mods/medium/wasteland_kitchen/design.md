## Mod設計書: Wasteland Kitchen（荒地の保存食）

### 仕様書から継承
- **目的**: 既存の `mixed_grain_bar` は単品の高カロリー食。本modは狩猟・採集・廃墟で手に入る素材から、保存性と満足度の異なる保存食を追加する。
- **スコープ**:
  - 含むもの: 完成食4種＋各レシピ4件。中間素材は作らず、バニラの `tallow` / `dry_meat` 等を流用。tool/qualityはバニラの調理器具を流用。
  - 含まないもの: 新規作物、農業システム、新規調理器具のC++効果、電気冷蔵、既存食の改変、中間素材の新規追加。
- **成功基準**: 4種をクラフトでき、比較表で各食品の差別化を説明できる。腐敗時間・カロリー・満足度が設計値通り。Level1/2通過、Level3でクラフト・喫食・腐敗時間・セーブ/ロード確認。

### ターゲットバージョン
- CDDA: 0.I RC（確認checkout: `f044a1c7c4f6184c129ce6dacff99ea573df326a`。計画書の `46730b6` と異なるため本設計のgrep結果を正とする）

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧（4種固定）
| 種別 | ID | copy-from | 差別化の方向 |
|---|---|---|---|
| ITEM/COMESTIBLE | `wk_pressed_ration` | `pemmican` | 保存食中の最大カロリー密度・360日・fun低 |
| ITEM/COMESTIBLE | `wk_smoked_cheese` | `cheese_hard` | 乳製品の長期保存・fun中 |
| ITEM/COMESTIBLE | `wk_trail_mix` | `granola` | 加熱不要・高fun・中保存 |
| ITEM/COMESTIBLE | `wk_field_stew` | `chili` | 高fun・短保存・缶詰活用 |
| recipe | `wk_pressed_ration` | —（`result` が識別子） | カテゴリ・activity_levelを明記 |
| recipe | `wk_smoked_cheese` | —（同上） | 同上 |
| recipe | `wk_trail_mix` | —（同上） | 同上 |
| recipe | `wk_field_stew` | —（同上） | 同上 |

`copy-from`先は1つに固定する。「系」表記は禁止。適切な親がなければ `copy-from` なし＋全フィールド表にする。

### 0.Iスキーマ
- 種別は `"type": "ITEM"` + `"subtypes": [ "COMESTIBLE" ]`。`type: "COMESTIBLE"` は使わない。
- フィールドは `calories` / `spoils_in` / `fun` / `vitamins` / `comestible_type`。`spoilage` / `enjoyability` は使わない。
- `charges` は液体・複数回分のみ任意。固体食品には付けない。
- `name` は質量名詞なら `{"str_sp": "..."}`、可算名詞なら `{"str": "...", "str_pl": "..."}`。バニラの同カテゴリ例に合わせる。
- 親から継承する `flags` / `vitamins` / `container` / `charges` を一覧化し、上書きするものだけ明記する。

### 親からの継承と上書き
| 食品 | 親 | 継承するもの | 上書きするもの |
|---|---|---|---|
| `wk_pressed_ration` | `pemmican` | `vitamins`、`container`（`bag_plastic_small`）、`material`（親にflagsなし） | `name` / `calories` / `spoils_in` / `fun` |
| `wk_smoked_cheese` | `cheese_hard` | `flags`（`NUTRIENT_OVERRIDE`）、`container`（`wrapper`）、`vitamins` | `name` / `calories` / `spoils_in` / `fun` |
| `wk_trail_mix` | `granola` | `flags`（`EDIBLE_FROZEN`）、`container`（`bag_plastic_small`）、`vitamins`、`material` | `name` / `calories` / `spoils_in` / `fun` |
| `wk_field_stew` | `chili` | `flags`（`EATEN_HOT`）、`container`（`can_medium`）、`vitamins`、`material` | `name` / `calories` / `spoils_in` / `fun` |

### レシピ必須項目
| 項目 | `wk_pressed_ration` | `wk_smoked_cheese` | `wk_trail_mix` | `wk_field_stew` |
|---|---|---|---|---|
| 親レシピ（準拠元） | `pemmican` | `cheese_hard` | `granola` | `chili` |
| `category` / `subcategory` | `CC_FOOD` / `CSC_FOOD_MEAT` | `CC_FOOD` / `CSC_FOOD_OTHER` | `CC_FOOD` / `CSC_FOOD_OTHER` | `CC_FOOD` / `CSC_FOOD_MEAT` |
| `skill_used` / `difficulty` | cooking 5（ドラフト） | cooking 5（ドラフト） | cooking 3（ドラフト） | cooking 2（ドラフト） |
| `time` | 45 m（ドラフト） | 1 h（ドラフト） | 45 m（ドラフト） | 20 m（ドラフト） |
| `tools` | `surface_heat` | `surface_heat`＋調理qualities | 加熱不要（`surface_heat`なし） | `surface_heat` |
| `activity_level` | `LIGHT_EXERCISE` | `LIGHT_EXERCISE` | `LIGHT_EXERCISE` | `LIGHT_EXERCISE` |
| `autolearn` | `true`（ドラフト） | `true`（ドラフト） | `true`（ドラフト） | `true`（ドラフト） |
| `components`方針 | `tallow` / `dry_meat`系＋穀物 | 乳系＋凝固剤（`salt`等、ドラフト） | `dry_meat`＋果物・穀物 | 肉＋野菜＋`can_medium`活用 |

- `charges` / `result_mult` は固体4種のため不要。`container` / `contained` は「親からの継承と上書き」表の通り。
- `wk_field_stew` の親は `chili` に固定する（`soup_meat` はDRINK/chargesのため使わない）。

### 比較表
既存品の実測値（設計の基準値）:

| 食品 | calories | weight / volume（1食分） | `spoils_in` | fun | vitamins（抜粋） | `charges` | container | 材料 | 特徴 |
|---|---|---|---|---|---|---|---|---|---|
| `pemmican` | 440 | 106 g / 120 ml | 360日 | 3 | vitC 3 / iron 21 | — | bag_plastic_small | flesh, fruit | 高カロリー長期保存 |
| `hardtack` | 280 | 70 g / 70 ml | 360日 | -4 | iron 15 | — | なし | wheat | 超長期・不味い |
| `jerky` | 348 | 85 g / 250 ml | 42日 | 4 | iron 26 | — | bag_plastic_small | — | 中保存 |
| `cheese_hard` | 135 | 34 g / — | 180日 | 5 | calcium 32 | — | wrapper | — | 乳製品・高fun |
| `granola` | 157 | 32 g / 62 ml | 180日 | 3 | iron 7 | — | bag_plastic_small | wheat, fruit | 長保存・加熱要 |
| `chili` | 299 | 253 g / 250 ml | 1日 | 5 | vitC 7 / iron 27 | — | can_medium | flesh, veggy, bean, tomato | 高fun・要加熱・短命 |
| `dry_meat` | —（素材） | 85 g / 125 ml | 360日 | — | meat_allergen | — | なし | flesh | 脱水肉素材 |
| `meat_smoked` | —（素材） | — / — | 42日 | 5 | — | — | なし | — | 燻製素材 |
| `tallow` | 496 | 55 g / 62 ml | 60日 | -18 | meat_allergen | — | なし | flesh | 超高カロリー・不味い |

新食品の設計値（ドラフト。Level3未確認のため確定しない）:

| 食品 | calories | weight / volume（1食分、ドラフト） | `spoils_in` | fun | vitamins（ドラフト） | `charges` | 材料（ドラフト） | 差別化（長所と短所の組） |
|---|---|---|---|---|---|---|---|---|
| `wk_pressed_ration` | 650 | 150 g / 150 ml | 360日 | -2 | iron（親準拠） | — | flesh, wheat | 保存食中の最大カロリー密度（4.33/gで親超え）。代償にfun低 |
| `wk_smoked_cheese` | 210 | 100 g / 100 ml | 180日 | 4 | calcium（親準拠） | — | milk | 乳製品の長期保存＋高calcium。代償に調理難度高 |
| `wk_trail_mix` | 320 | 120 g / 250 ml | 90日 | 7 | iron（親準拠） | — | fruit, wheat, flesh | 加熱不要・高fun。代償に中保存・材料多種 |
| `wk_field_stew` | 350 | 300 g / 300 ml | 2日 | 8 | vitC, iron（親準拠） | — | flesh, veggy＋`can_medium` | 最高fun・缶詰活用。代償に短命・要加熱 |

`charges` がある食品は per-charge と total を区別する。weight / volume も per-portion と total を区別する（現行の比較対象9種に `charges` 持ちはない）。
「既存品にない数値」ではなく「既存品と異なる長所と短所の組」で差別化を説明する。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/items/comestibles/meat_dishes.json` — `pemmican`（440 / 360日 / fun 3）、`chili`（299 / 1日 / fun 5）、`dry_meat`（360日）
- [x] `external/cdda/data/json/items/comestibles/bread.json` — `hardtack`（280 / 360日 / fun -4）
- [x] `external/cdda/data/json/items/comestibles/carnivore.json` — `jerky`（348 / 42日 / fun 4）、`tallow`（496 / 60日 / fun -18）、`meat_smoked`（42日 / fun 5）
- [x] `external/cdda/data/json/items/comestibles/dairy.json` — `cheese_hard`（135 / 180日 / fun 5）
- [x] `external/cdda/data/json/items/comestibles/wheat.json` — `granola`（157 / 180日 / fun 3）
- [x] `external/cdda/data/json/vitamin.json` — 使用vitaminの実在確認
- [x] `external/cdda/data/json/flags.json` — `EATEN_HOT` / `EDIBLE_FROZEN` / `INEDIBLE` / `NUTRIENT_OVERRIDE` / `SMOKED` 実在
- [x] レシピ: `recipes/food/meat_dishes.json`（pemmican, chili。`LIGHT_EXERCISE`）、`bread.json`（hardtack）、`carnivore.json`（jerky）、`dairy_products.json`（cheese_hard。`COOK` 3＋`BOIL` 2等）、`wheat.json`（granola）、`dry.json`（dry_meat。`NO_EXERCISE`＋`dehydrating_heat`）
- [x] `external/cdda/data/json/materials.json` — `flesh` / `fruit` / `wheat` / `milk` 等の実在確認（`dairy` はmaterialに存在しない）
- [x] `mods/small/mixed_grain_bar/` — 既存mod（`mgb_mixed_grain_bar` 単品高カロリー食）との差別化確認。本modは保存性・満足度の異なる4種展開で差別化する

### ファイル構成
```
mods/medium/wasteland_kitchen/
├── modinfo.json
├── spec.md
├── design.md
└── data/
    ├── items.json    # COMESTIBLE 4点
    └── recipes.json  # recipe 4点
```

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json
- 各編集後に Level1。逸脱はその都度 design.md に反映。

### テスト手順
1. `bash scripts/validate.sh mods/medium/wasteland_kitchen` でJSON構文チェック（Level1）
2. `bash scripts/place_mod_for_test.sh --dry-run mods/medium/wasteland_kitchen` で既存配置を確認→`--force` で配置
3. `bash scripts/check_mods.sh --isolated --check-errors wasteland_kitchen` でmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認: デバッグスポーン／クラフト／喫食／腐敗時間／セーブロード

### 完了条件
- [ ] Level1: JSON構文OK（未実行、本設計は未実装）
- [ ] Level2: 起動OK（未実行、本設計は未実装）
- [ ] Level3: クラフト・喫食・腐敗確認（未実行、本設計は未実装）
- [ ] `design.md` が実装値と一致（実装時に更新）

### リスク
- 栄養・腐敗・満足度のバランス、既存食品との重複。比較表で差別化できない食品は設計ドラフト前に差し替える。
- `name` の複数形エラー（`str_sp` vs `str`＋`str_pl` の選択ミス）。
- 継承flagsの意図しない引き継ぎ（「親からの継承と上書き」表の通り適用。`INEDIBLE` はどの食品も継承しない）。
- 新食品の設計値はドラフト。Level3未確認のためバランス確定はしない。

### ID衝突確認記録
- 新規ID（`wk_*` 8件）は `external/cdda/data/json` と `mods/` に存在せず、衝突なし。
- JSON実装は行わない。`modinfo.json` / `data/*.json` は未作成。Level1/2/3未実行。
