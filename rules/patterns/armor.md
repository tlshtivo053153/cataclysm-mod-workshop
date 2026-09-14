# 防具（ARMOR）実装パターン

CDDA 0.I RC で `ARMOR` subtype の防具を追加する際のパターン。
実装例: `mods/small/bone_armor/`

## 概要

防具は `"type": "ITEM"` + `"subtypes": [ "ARMOR" ]` で定義する。base に 2,900 件以上存在するため、
**新規追加前に既存防具との重複を必ず確認する**（`helmet_scrap`, `armguard_scrap`, `armor_junk_plate` 等の
廃材防具は既に存在する）。

## ファイル構成

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | `category: "items"` または `"misc_additions"` |
| `data/items.json` | `ITEM` (ARMOR) | 防具定義 ×N |
| `data/recipes.json` | `recipe` | 製作レシピ ×N |

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/items/armor/suits_protection.json` | 胴防具（`armor_chitin`, `armor_larmor` 等） |
| `data/json/items/armor/helmets.json` | 兜（`helmet_chitin`, `helmet_army`, `helmet_scrap` 等） |
| `data/json/items/armor/arms_armor.json` | 腕防具（`armguard_chitin`, `armguard_lightplate` 等） |
| `data/json/items/armor/legs_armor.json` | 脚防具 |
| `data/json/materials.json` | マテリアルID（`bone`, `steel`, `leather`, `chitin` 等） |
| `data/json/recipes/armor/suit.json` / `arms.json` | 防具レシピの書式・`activity_level`・カテゴリ |

## 防具アイテムの基本構造

```json
{
  "type": "ITEM",
  "subtypes": [ "ARMOR" ],
  "id": "bna_bone_helmet",
  "copy-from": "helmet_chitin",
  "name": { "str": "bone helmet" },
  "weight": "1700 g",
  "volume": "2800 ml",
  "material": [ "bone", "leather" ],
  "material_thickness": 4,
  "warmth": 15,
  "color": "light_gray",
  "flags": [ "STURDY" ],
  "armor": [
    {
      "covers": [ "head" ],
      "coverage": 95,
      "encumbrance": 20,
      "specifically_covers": [ "head_crown", "head_forehead" ]
    }
  ]
}
```

### `armor` 配列のフィールド

| フィールド | 説明 |
|---|---|
| `covers` | 部位（`torso`, `head`, `arm_l`, `arm_r`, `leg_l`, `leg_r`, `hand_l`, `hand_r`, `foot_l`, `foot_r`, `eyes`, `mouth`） |
| `coverage` | 被覆率（0〜100） |
| `encumbrance` | 着用時の動作ペナルティ。配列 `[ 最小, 最大 ]` も可 |
| `encumbrance_modifiers` | `[ "NONE" ]` で「装備しても荷重ペナルティなし」（軍用ヘルメット等） |
| `specifically_covers` | サブ部位（`head_crown`, `leg_upper_r` 等）。`data/json/body_parts.json` 参照 |
| `cover_melee` / `cover_ranged` / `cover_vitals` | 部位別の被覆率（省略時は `coverage`） |
| `rigid_layer_only` | 硬質レイヤーのみ有効（`mouth`, `eyes` 等で使用） |
| `material` | 部位ごとの素材（`[{ "type": "leather", "covered_by_mat": 100, "thickness": 4.5 }]` 配列。省略時はアイテム直下の `material` + `material_thickness` が使われる） |

### 素材指定の2方式

1. **アイテム直下方式**（`armor_chitin` 系）: `material` + `material_thickness` を直下に書き、`armor` 配列では素材を書かない。copy-from で素材だけ差し替えたい場合はこちらが簡単
2. **部位ごと方式**（`armor_larmor` 系）: 各 `armor` エントリの `material` に `covered_by_mat` と `thickness` を書く。部位ごとに厚みを変えられる

> `copy-from` で素材を差し替える場合、親が部位ごと方式だと `armor` 配列側の素材が残るため防護値が変わらない。
> **親がアイテム直下方式かどうかを必ず確認する。**

## name の複数形ルール（0.I で厳格化）

0.I では翻訳ローダーが複数形を検証する。**間違えるとゲーム起動時にエラー**になる。

| ケース | 書式 | 例 |
|---|---|---|
| 自動生成できる語 | `{ "str": "bone helmet" }`（`str_pl` は**付けない**） | `str_pl` を付けると「不要」エラー |
| 自動生成できない語（語尾が s / 不規則） | `{ "str": "bone cuirass", "str_pl": "bone cuirasses" }` | `str` のみだと「複数形を生成できない」エラー |
| 単複同形 | `{ "str_sp": "..." }` | — |

- `pair of ...` のような数量表現は `str_pl` が必須（例: `{ "str": "pair of bone arm guards", "str_pl": "pairs of bone arm guards" }`）
- ARMOR は base でも `str` 形式が主流

## レシピ

```json
{
  "type": "recipe",
  "activity_level": "LIGHT_EXERCISE",
  "result": "bna_bone_cuirass",
  "category": "CC_ARMOR",
  "subcategory": "CSC_ARMOR_TORSO",
  "skill_used": "tailor",
  "difficulty": 4,
  "skills_required": [ [ "fabrication", 2 ] ],
  "time": "2 h",
  "autolearn": true,
  "qualities": [ { "id": "CUT", "level": 1 }, { "id": "LEATHER_AWL", "level": 1 } ],
  "components": [ [ [ "bone", 10 ] ], [ [ "leather", 4 ] ], [ [ "cordage_short", 6, "LIST" ] ] ]
}
```

- `activity_level` は必須。防具は `LIGHT_EXERCISE`（革・布・骨）〜 `BRISK_EXERCISE`（板金鍛造）
- サブカテゴリ: `CSC_ARMOR_TORSO` / `CSC_ARMOR_HEAD` / `CSC_ARMOR_ARMS` / `CSC_ARMOR_LEGS` / `CSC_ARMOR_FEET` / `CSC_ARMOR_HANDS` / `CSC_ARMOR_SUIT`

## チェックリスト

- [ ] base に同名・同性能の防具が存在しないか確認した（`helmet_scrap`, `armor_junk_plate` 等）
- [ ] `subtypes: [ "ARMOR" ]` を明示した
- [ ] `name` の複数形ルールを満たしている（不要な `str_pl` はエラー）
- [ ] `material` は `materials.json` に実在する素材を使った
- [ ] copy-from 親の `armor` 配列の素材方式（直下/部位ごと）を確認した
- [ ] レシピに `activity_level` を設定した
- [ ] レシピの `subcategory` が `CSC_ARMOR_*` に実在する
- [ ] `bash scripts/validate.sh` → `check_mods.sh --check-errors` を通過した
