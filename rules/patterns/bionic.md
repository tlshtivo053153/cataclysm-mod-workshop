# Bionics (CBM) 実装パターン

CDDAに新規バイオニック（CBM）を追加するためのパターンファイル。

## 概要

CBM（Compact Bionic Module）を追加する場合、bionic定義とCBMアイテムを**同一ID**で二重定義する：

- **bionic定義** (`"type": "bionic"`): 埋め込み後の機能（パッシブ能力・起動効果・消費電力等）
- **CBMアイテム** (`"type": "ITEM"`, `"subtypes": [ "BIONIC_ITEM" ]`): 埋め込み前のアイテム（重量・難易度・価格等）

CDDAは両方の定義を同じIDで解決し、埋め込み時に対応付けを行う。

## ファイル構成

小規模バイオニックmod（bionic 2〜4種）の最小構成：

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "misc"` 推奨 |
| `data/bionics.json` | `bionic` | bionic定義 ×N（機能・効果定義） |
| `data/items.json` | `ITEM` (BIONIC_ITEM) | CBMアイテム ×N（copy-from: `bionic_general_npc_usable`） |
| `data/itemgroups.json` | `item_group` | loot出現テーブル拡張（copy-from + extend） |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/bionics.json` | 全bionic定義（128種）。`bio_power_storage`, `bio_armor_torso`, `bio_str_enhancer` 等の構造確認 |
| `data/json/items/bionics.json` | 全CBMアイテム定義。抽象ベース `bionic_general`, `bionic_general_npc_usable`, `bionic_general_faulty` |
| `data/json/itemgroups/bionics.json` | bionic関連アイテムグループ。`bionics`（collection型・101件）, `bionics_common`（distribution型・20件）, `bionics_mil` |
| `data/json/body_parts.json` | 各部位の `bionic_slots` 容量。torso=80, head=18, arm=~30, leg=~30, hand=~7, eyes=~4 |
| `data/json/items/generic.json` | `burnt_out_bionic`（looks_like用の粗悪な見た目ID） |
| `doc/JSON/JSON_INFO.md` (L1317〜) | bionic型の全フィールドリファレンス |

## 二重定義パターン

bionic定義とCBMアイテムは同じIDで定義する。CBMアイテムは抽象ベースから `copy-from` する：

### bionic定義（data/bionics.json）

```json
[
  {
    "id": "bio_my_bionic",
    "type": "bionic",
    "name": { "str": "My Bionic" },
    "description": "An implanted device that does something useful.",
    "occupied_bodyparts": [ [ "torso", 5 ], [ "arm_l", 3 ] ],
    "flags": [ "BIONIC_TOGGLED", "BIONIC_NPC_USABLE" ],
    "act_cost": "10 J"
  }
]
```

### CBMアイテム定義（data/items.json）

```json
[
  {
    "id": "bio_my_bionic",
    "copy-from": "bionic_general_npc_usable",
    "type": "ITEM",
    "subtypes": [ "BIONIC_ITEM" ],
    "name": { "str": "My Bionic CBM" },
    "looks_like": "bio_int_enhancer",
    "description": "A compact module ready for implantation. Grants useful functionality.",
    "price": "100 USD",
    "price_postapoc": "10 USD",
    "weight": "500 g",
    "difficulty": 5
  }
]
```

## 抽象ベース

3種類の抽象ベースから選択し `copy-from` する：

| 抽象ID | 用途 | 主なフィールド |
|---|---|---|
| `bionic_general` | 基本。簡易なバイオニック向け | `use_action: [ "install_bionic" ]`, `faults: [ { "fault": "fault_bionic_salvaged" } ]`, `flags: [ "CBM", "FRAGILE_MELEE" ]` |
| `bionic_general_npc_usable` | NPCも使用可能 | `bionic_general` を継承 + `flags: [ "BIONIC_NPC_USABLE" ]` 追加 |
| `bionic_general_faulty` | 故障CBM専用 | `bionic_general` を継承 + 価格ゼロ・軽量化・description変更 |

**ほとんどの新規CBMは `bionic_general_npc_usable` から `copy-from` する。**

`bionic_general_npc_usable` は `bionic_general` から以下を継承する：
- `use_action: [ "install_bionic" ]` — 埋め込みアクション
- `faults: [ { "fault": "fault_bionic_salvaged" } ]` — サルベージ品故障リスク
- `material: [ "steel", "plastic" ]`, `symbol: ":"`, `color: "yellow"`
- `category: "bionics"`, `flags: [ "CBM", "FRAGILE_MELEE", "BIONIC_NPC_USABLE" ]`

## bionic定義の主要フィールド

### 必須フィールド
- `id`: CBMアイテムと同一ID。命名規則は後述。
- `type`: 必ず `"bionic"`
- `name`: `{ "str": "名称" }` 形式
- `description`: フレーバーテキスト

### power系（パワーストレージ）
```json
{
  "id": "bio_junk_power_storage",
  "capacity": "50 kJ",
  "dupes_allowed": true
}
```
- `capacity`: 増加する最大バイオニックパワー。単位付き文字列（`"kJ"` 等）
- `dupes_allowed`: 同一パワーストレージを複数埋め込み可能か

### 起動コスト（アクティブbionic用）
```json
"act_cost": "5 J",       // 起動時のコスト
"react_cost": "1 kJ",    // 自動発動時のコスト
"trigger_cost": "2 kJ",  // リアクティブ発動時のコスト
"time": "1 s"            // ティック間隔
```

### パッシブ発電（燃料型）
```json
"fuel_options": [ "alcohol" ],
"fuel_efficiency": 0.5,
"exothermic_power_gen": true,
"passive_pseudo_items": [ "internal_ethanol_tank" ]
```

### enchantments（ステータス強化・効果）
```json
// 常時ステータス上昇
"enchantments": [ { "values": [ { "value": "STRENGTH", "add": 2 } ] } ]

// 起動時のみ
"enchantments": [ { "condition": "ACTIVE", "values": [ { "value": "DEXTERITY", "add": 1 } ] } ]

// 乗算
"enchantments": [ { "values": [ { "value": "RECOIL_MODIFIER", "multiply": -0.35 } ] } ]

// スキル強化
"enchantments": [ { "skills": [ { "value": "throw", "add": 5 } ] } ]
```

### occupied_bodyparts（スロット消費）
```json
"occupied_bodyparts": [
  [ "torso", 6 ],
  [ "arm_l", 4 ],
  [ "arm_r", 4 ],
  [ "leg_l", 8 ],
  [ "leg_r", 8 ]
]
```
各部位の消費スロット数。`body_parts.json` の容量を超えないこと。

スロット容量目安: torso=80, head=18, arm=30, leg=30, hand=7, foot=7, eye=4, mouth=5

### protec（防御）
```json
// 物理防御
"protec": [
  [ "torso", { "bash": 3, "cut": 3, "bullet": 3, "stab": 3 } ]
]
// 属性防御
"protec": [
  [ "hand_l", { "electric": 3 } ]
]
```

### encumbrance（機動性ペナルティ）
```json
"encumbrance": [ [ "torso", 1 ], [ "hand_l", 3 ], [ "hand_r", 3 ] ]
```

### fake_weapon（武器型bionic）
```json
// 遠隔武器 (BIONIC_GUN)
{
  "fake_weapon": "bio_lightning",
  "flags": [ "BIONIC_GUN" ]
}
// 近接武器 (BIONIC_WEAPON)
{
  "fake_weapon": "bio_claws_weapon",
  "flags": [ "BIONIC_TOGGLED", "BIONIC_WEAPON" ]
}
```

### pseudo_items（内部ツール）
```json
// 常時利用可能なツール
"passive_pseudo_items": [ "toolset", "integrated_welder" ],
// 起動時のみ利用可能
"toggled_pseudo_items": [ "electrohack" ]
```

### 変異関連
```json
// インストール時に自動キャンセルされる変異
"canceled_mutations": [ "VINES1", "VINES2", "VINES3" ],
// 共存不可の変異
"mutation_conflicts": [ "M_SKIN", "SCALES", "CHITIN", "FEATHERS" ]
```
- `canceled_mutations`: 指定した変異が自動で除去される
- `mutation_conflicts`: 指定した変異があるとインストール不可
- `mutation_conflicts` のIDは `data/json/mutations/mutations.json` で実在確認すること

### アップグレード
```json
// ベース側
"available_upgrades": [ "bio_my_upgrade" ],
// アップグレード先
"upgraded_bionic": "bio_my_base"
```

### included_bionics（同時埋め込み）
```json
"included_bionics": [ "bio_earplugs" ]
```
指定した bionic ID が自動的に同時埋め込みされる。耳栓・目隠し等の組み合わせバイオニックで使用。

### active_flags（起動時キャラクターフラグ）
```json
"active_flags": [ "BLIND", "DEAF" ]
```
BIONIC_TOGGLED と併用し、起動時に指定したキャラクターフラグを付与する。

### EOC（Effect on Condition）
```json
"activated_eocs": [ "EOC_bio_adrenaline" ]
```

### social_modifiers
```json
"social_modifiers": { "persuade": -20, "lie": 10, "intimidate": 20 }
```

## 主要bionicフラグ

| フラグ | 意味 |
|---|---|
| `BIONIC_TOGGLED` | ON/OFF切り替え可能 |
| `BIONIC_NPC_USABLE` | NPCが使用可能 |
| `BIONIC_SLEEP_FRIENDLY` | 睡眠中も機能 |
| `BIONIC_SHOCKPROOF` | 電撃（EMP）無効。**金属製bionicでは付けない** |
| `BIONIC_FAULTY` | 故障bionic（メリットのない欠陥品） |
| `BIONIC_POWER_SOURCE` | バイオニックパワー発電 |
| `BIONIC_WEAPON` | 近接武器型bionic |
| `BIONIC_GUN` | 遠隔武器型bionic |
| `USES_BIONIC_POWER` | バイオニックパワー消費 |
| `NO_UNWIELD` | 武器の持ち替え不可 |

## CBMアイテム定義の主要フィールド

`copy-from: "bionic_general_npc_usable"` により継承されるフィールドを除き、以下の差分のみ記述する：

```json
{
  "id": "bio_mymod_x",
  "copy-from": "bionic_general_npc_usable",
  "type": "ITEM",
  "subtypes": [ "BIONIC_ITEM" ],
  "name": { "str": "My Bionic CBM" },
  "looks_like": "bio_int_enhancer",
  "description": "A bionic module ready for installation.",
  "price": "100 USD",
  "price_postapoc": "10 USD",
  "weight": "500 g",
  "difficulty": 5
}
```

| フィールド | 説明 |
|---|---|
| `name` | CBMアイテム名。**末尾に " CBM" を付ける**（バニラの慣習） |
| `looks_like` | 見た目のフォールバック。通常 `"bio_int_enhancer"`、粗悪品は `"burnt_out_bionic"` |
| `difficulty` | 埋め込み難易度（1〜）。低いほど簡単。バニラ例: power_storage=1, armor_torso=6, str_enhancer=11 |
| `price_postapoc` | 終末後の取引価格 |
| `weight` | 単位付き（`"500 g"` 形式）。軽量なpower_storage=70g、重量級armor_torso=3000g |
| `faults` | **継承されるため記述不要。** `bionic_general` の `fault_bionic_salvaged` が適用される |
| `use_action` | **継承されるため記述不要。** `[ "install_bionic" ]` が適用される |
| `volume` | **継承されるため記述不要。** `bionic_general` の `"2500 ml"` が適用される |
| `is_upgrade` | **継承されるため記述不要。** `bionic_general` の `false` が適用される。アップグレードCBMのみ `true` を指定 |

## アイテムグループへの追加（loot出現）

バイオニックの入手経路として、3つの標準グループがある：

| グループID | subtype | 選出方式 | 用途 |
|---|---|---|---|
| `bionics` | collection（デフォルト） | 全エントリ出現 | 確定ドロップ（施設の固定配置等） |
| `bionics_common` | `"distribution"` | 1個ランダム選択（重み付け） | ランダムドロップ（低〜中グレード） |
| `bionics_mil` | collection | 全エントリ出現 | 軍事施設の固定ドロップ |

### 小規模modでは `bionics_common` への extend が推奨

```json
[
  {
    "type": "item_group",
    "id": "bionics_common",
    "copy-from": "bionics_common",
    "extend": {
      "items": [
        [ "bio_my_bionic", 10 ],
        [ "bio_my_rare_bionic", 5 ]
      ]
    }
  }
]
```

- `bionics_common` は distribution型 → **subtype の再宣言は不要**
- 各エントリ: `[ "CBM_ID", 重み ]`。重み10が標準、5でややレア
- 同じmodのCBMは重み5〜10が目安（バニラ20件とのバランス）

### bionics（collection型）への追加も可能

```json
[
  {
    "type": "item_group",
    "id": "bionics",
    "copy-from": "bionics",
    "extend": {
      "items": [ [ "bio_my_bionic", 10 ] ]
    }
  }
]
```
collection型のため subtype 再宣言不要。重みは事実上無視される（全エントリ出現）。

## クラフトレシピ（オプション）

バニラCDDAではCBMのクラフトレシピは存在しない。レシピを追加する場合は
Aftershock mod (`data/mods/Aftershock/recipes/bionic_recipes.json`) を参考にする。

```json
{
  "type": "recipe",
  "activity_level": "LIGHT_EXERCISE",
  "result": "bio_power_storage",
  "category": "CC_ELECTRONIC",
  "subcategory": "CSC_ELECTRONIC_CBMS",
  "skill_used": "electronics",
  "skills_required": [ "firstaid", 5 ],
  "difficulty": 6,
  "time": "4 h",
  "reversible": true,
  "book_learn": [ [ "recipe_lab_elec", 5 ] ],
  "using": [ [ "soldering_standard", 20 ] ],
  "qualities": [
    { "id": "SCREW_FINE", "level": 1 },
    { "id": "BIONIC_ASSEMBLY", "level": 2 }
  ],
  "components": [
    [ [ "burnt_out_bionic", 1 ] ],
    [ [ "e_scrap", 10 ] ]
  ]
}
```

- `qualities` には `BIONIC_ASSEMBLY`（Autodoc等）が必須
- `components` には `burnt_out_bionic` を最低1個含めるのが慣例
- `subcategory`: `"CSC_ELECTRONIC_CBMS"` でクラフトメニューのCBMカテゴリに表示される

## 命名規則

| 種別 | プレフィックス | 例 |
|---|---|---|
| バニラCBM | `bio_` | `bio_power_storage`, `bio_shock`, `bio_ethanol` |
| 故障CBM | `bio_faulty_` または `bio_<症状>` | `bio_faulty_electromagnetic_leak`, `bio_sleepy` |
| バニラ抽象 | プレフィックスなしの一意なID | `bionic_general`, `bionic_general_npc_usable` |
| mod固有CBM | `bio_modprefix_` | `bio_junk_power_storage`, `afs_bio_missiles` |
| CBMアイテム名末尾 | `" CBM"` | `"Power Storage CBM"`, `"My Bionic CBM"` |

**bionic定義のIDとCBMアイテムのIDは必ず同一にする。**

## 実装チェックリスト

- [ ] bionic定義とCBMアイテムが同一IDか
- [ ] CBMアイテムの `copy-from` が `bionic_general_npc_usable`（または適切な抽象ベース）か
- [ ] `name` 形式が正しいか: bionic → `{ "str": "..." }`, CBM名末尾 `" CBM"`
- [ ] `occupied_bodyparts` の各部位スロット数が `body_parts.json` の容量を超えていないか
- [ ] `mutation_conflicts` のIDが `data/json/mutations/mutations.json` に実在するか
- [ ] 重量・容量が単位付き文字列形式（`"500 g"`, `"2500 ml"`）か
- [ ] `bionics_common` extend 時に subtype 再宣言をしていないか（distribution型の場合）
- [ ] `BIONIC_SHOCKPROOF` フラグの要否を検討したか（金属製なら付けない）
- [ ] `faults` フィールドをCBMアイテムに書いていないか（抽象ベースから継承される）
- [ ] modinfo.json の `dependencies: [ "dda" ]` が正しいか
