# GUNMOD 実装パターン

CDDAに新規武器アタッチメント（GUNMOD）を追加するためのパターンファイル。

## 概要

GUNMOD は `"type": "ITEM"` + `"subtypes": ["GUNMOD"]` で定義する。銃器の性能を変更するアタッチメント。

## ファイル構成

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報 |
| `data/items.json` | `ITEM` (GUNMOD) | アタッチメントアイテム定義 |
| `data/recipes.json` | `recipe` | クラフトレシピ（オプション） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/items/gunmod/underbarrel.json` | bipod系GUNMODの実装参照 |
| `data/json/items/gunmod/mount.json` | アダプター系GUNMOD（`add_mod`使用例） |
| `data/json/items/gun/` | 装着先の銃が持つ `valid_mod_locations` 確認 |
| `data/json/recipes/weapon/mods.json` | 武器modレシピの実装参照 |

## 基本パターン: バニラbipodからの派生

```json
[
  {
    "type": "ITEM",
    "subtypes": [ "GUNMOD" ],
    "id": "mymod_scrap_bipod",
    "name": { "str": "scrap bipod" },
    "description": "A crude bipod made from scrap metal and duct tape.  It attaches to the front of a long arm and provides some stability when aiming, though it's heavier and less effective than a proper bipod.",
    "weight": "700 g",
    "volume": "500 ml",
    "integral_volume": "0 ml",
    "integral_weight": "0 g",
    "price": "10 USD",
    "price_postapoc": "2 USD",
    "install_time": "30 m",
    "material": [ "steel" ],
    "symbol": ":",
    "color": "dark_gray",
    "location": "underbarrel",
    "mod_targets": [ "rifle", "launcher", "smg", "shotgun", "crossbow" ],
    "handling_modifier": 6,
    "melee_damage": { "bash": 6 },
    "flags": [ "BIPOD", "SLOW_WIELD" ],
    "min_skills": [ [ "weapon", 1 ] ]
  }
]
```

## 主要フィールド解説

### name
- GUNMOD は `{"str": "名称"}` 形式（TOOL相当。`str_sp` ではない）
- バニラ全GUNMODが `str` 形式を使用

### type / subtypes
- `"type": "ITEM"` + `"subtypes": ["GUNMOD"]` が必須
- 0.I では旧 `"type": "GUNMOD"` 構文は廃止済み

### location と mod_targets の相互関係（最重要）

gunmod の `location` は、装着先の銃の `valid_mod_locations` に含まれるエントリと**完全一致**する必要がある。

**`"underbarrel"` と `"underbarrel mount"` は別スロット**：
- `"underbarrel"` → 直接装着可能なスロット。一部の新型ライフル（AR-15系、scar_l 等）が持つ
- `"underbarrel mount"` → アダプター用スロット。多くの最新銃が持つ（95+銃器）。バニラの `underbarrel_mount` アダプターを装着すると `"underbarrel"` スロットが追加（`add_mod`）され、間接的にバイポッドを装着可能になる

**mod_targets は広めに設定する**：
- バニラ `bipod` は `["rifle", "launcher", "smg", "shotgun", "crossbow"]` で広範な互換性を確保
- `["rifle"]` のみに絞ると、実際に `location` を持つ銃が少なくなり装着不可になる
- 新規GUNMODを作る際は、必ず同種のバニラGUNMODの `mod_targets` を参照すること

### integral_volume / integral_weight
- 装着時に銃の容量・重量から差し引かれる値
- バイポッドのように**追加のアタッチメント**の場合は `"0 ml"` / `"0 g"`（装着しても占有しない＝全体重がカウントされる）
- ハンドガードのように**既存パーツを置換**する場合は実際の容量・重量を設定（装着前のパーツ分が差し引かれる）

### min_skills（ITEM側） vs skills_required（recipe側）
- `min_skills` は**GUNMODアイテム定義**に記述し、**銃への装着難易度**を制御する
- `skills_required` は**レシピ定義**に記述し、**クラフト難易度**を制御する
- 両者は独立しており、異なるスキル・レベルを設定できる

### handling_modifier
- 射撃時のハンドリング（反動制御）補正値
- バニラ参考値：
  - `bipod`（展開時）: 18
  - `scout_bipod`（展開時）: 12
  - `bipod_handguard`（格納時）: 4
  - `arisaka_monopod`（格納時）: 6
  - `grip`（フォアグリップ）: 6
  - `grip_mod`（軽量グリップ）: 6

### install_time
- 銃への装着にかかる時間
- バニラ参考値：`bipod` = `"1 m"`, `bipod_handguard` = `"20 m"`, `grip` = `"30 s"`, `grip_mod` = `"15 m"`

### flags
- 展開状態のバイポッド系GUNMODが持つ共通フラグ: `"BIPOD"`, `"SLOW_WIELD"`（格納状態の `bipod_handguard`, `scout_bipod` は `BIPOD` を持たない）
- バニラ同種GUNMODのフラグを確認して合わせる
- 変形（展開/格納）なしの簡易バイポッドは `"BIPOD"` + `"SLOW_WIELD"` の2フラグ

### add_mod（アダプターの定義）
- GUNMODが装着先の銃に新たな `valid_mod_locations` を追加できる
- 例: `underbarrel_mount` は `"add_mod": [ [ "underbarrel", 1 ] ]` で `"underbarrel"` スロットを追加
- アダプターには `"IRREMOVABLE"` フラグを付与するのがバニラのパターン

## レシピ設計

### 武器modレシピのパターン

```json
[
  {
    "type": "recipe",
    "activity_level": "MODERATE_EXERCISE",
    "result": "mymod_scrap_bipod",
    "category": "CC_WEAPON",
    "subcategory": "CSC_WEAPON_MODS",
    "skill_used": "fabrication",
    "skills_required": [ [ "gun", 1 ] ],
    "difficulty": 1,
    "time": "15 m",
    "autolearn": true,
    "components": [
      [ [ "pipe", 1 ] ],
      [ [ "steel_chunk", 1 ] ],
      [ [ "duct_tape", 50 ] ]
    ]
  }
]
```

### レシピ設計指針

| 要素 | 指針 | 根拠 |
|---|---|---|
| `category` / `subcategory` | `CC_WEAPON` / `CSC_WEAPON_MODS` | バニラ bipod レシピ準拠 |
| `activity_level` | `MODERATE_EXERCISE` | バニラ bipod レシピ準拠 |
| `difficulty` | バニラより下げる。例：bipod 難易度4 → scrap bipod 難易度1 | 製作に必要な工具・技能を下げるため |
| `skills_required` | 入れ子配列 `[ ["gun", 1] ]` | 複数スキルの場合は入れ子、単一でも入れ子可 |
| `autolearn` | `true`（レシピ本不要） | 即席武器は自習可能が妥当 |
| `qualities` | 低スキル向けなら不要または最低限 | バニラ bipod は溶接工具が必要だが、低スキル版では省略 |

### components で AMMO アイテムを参照する場合
- `duct_tape` は `type: "ITEM", subtypes: ["AMMO"]` （`items/ammo.json`）
- レシピの `components` ではIDと個数のみで参照: `[ [ "duct_tape", 50 ] ]`
- テープ消費系のレシピに `ammo_type` の指定は不要（IDのみで十分）

## 実装チェックリスト

- [ ] `name` が `{"str": "..."}` 形式か（`str_sp` ではない）
- [ ] `type: "ITEM"` + `subtypes: ["GUNMOD"]` を明示しているか
- [ ] `location` が装着先の銃の `valid_mod_locations` に存在するか確認したか
  - `underbarrel` と `underbarrel mount` は別スロット。混同しないこと
- [ ] `mod_targets` がバニラ同種GUNMODと同等の広さか（狭すぎると装着不可になる）
- [ ] `min_skills`（装着難易度）と recipe `skills_required`（クラフト難易度）を適切に分けているか
- [ ] `integral_volume` / `integral_weight` がアタッチメントの性質（追加/置換）に合っているか
- [ ] 同種のバニラGUNMODを参照し、`flags`・`handling_modifier`・`melee_damage` の値を比較したか
- [ ] `install_time` のバランスが適切か（低スキル版は長めに設定）
- [ ] `symbol` が `:` か（標準GUNMODシンボル）
- [ ] recipe の `subcategory` が `CSC_WEAPON_MODS` か（`CSC_WEAPON_RANGED` は銃本体用）
- [ ] recipe の `activity_level` が設定されているか（0.I RC 必須）
- [ ] レシピの `components` で使用する全アイテムIDがバニラに存在するか
- [ ] description の英文がテキストスタイルチェッカーに準拠しているか（文区切りにダブルスペース）
