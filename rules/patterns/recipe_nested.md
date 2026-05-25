# Nested Category レシピ実装パターン

CDDAで `subcategory: "CSC_*_NESTED"` を使ったネストレシピを追加するためのパターンファイル。

## 概要

CDDAのクラフトシステムでは、関連するレシピをグルーピングしてクラフトメニューを整理するために **nested category** が使われる。変異原（mutagen）、弾薬、料理など多くのカテゴリで採用されている。

## アーキテクチャ

ネストシステムは2つの要素から成る：

### 1. Leaf recipe（子レシピ）

個別のレシピ定義。`category: "CC_*"`、`subcategory: "CSC_*_NESTED"` を指定する：

```json
{
  "type": "recipe",
  "activity_level": "LIGHT_EXERCISE",
  "result": "mutagen_insect",
  "category": "CC_*",
  "subcategory": "CSC_*_NESTED",
  "skill_used": "chemistry",
  "difficulty": 7,
  "...": "..."
}
```

**重要**: `CC_*` はワイルドカードカテゴリであり、このレシピは直接クラフトメニューに表示されない。`CSC_*_NESTED` は「このレシピは親の nested_category の中に含まれる」ことを示すシグナル。

### 2. Nested category（親カテゴリ）

`type: "nested_category"` で定義するクラフトメニューのエントリ。実際のクラフトカテゴリ（`CC_CHEM` 等）の下に配置され、含むレシピのIDを `nested_category_data` に列挙する：

```json
{
  "id": "nested_mutagen_formicid",
  "type": "nested_category",
  "activity_level": "LIGHT_EXERCISE",
  "category": "CC_CHEM",
  "subcategory": "CSC_CHEM_MUTAGEN",
  "name": "formicid mutagens",
  "description": "Recipes related to synthesizing formicid mutagenic substances.",
  "skill_used": "chemistry",
  "nested_category_data": [
    "mutagen_formicid",
    "iv_mutagen_formicid"
  ],
  "difficulty": 7
}
```

### フィールド解説

| フィールド | 必須 | 説明 |
|---|---|---|
| `id` | ○ | nested category の一意ID。バニラと衝突しないようにする |
| `type` | ○ | 常に `"nested_category"` |
| `activity_level` | ○ | レシピ群の代表的な運動強度。通常 Leaf recipe と同じ値を設定 |
| `category` | ○ | 実際のクラフトカテゴリ（`CC_CHEM`, `CC_FOOD`, `CC_AMMO` 等）。**`CC_*` は不可** |
| `subcategory` | ○ | 実際のサブカテゴリ（`CSC_CHEM_MUTAGEN`, `CSC_FOOD_MEAT` 等）。**`CSC_*_NESTED` は不可** |
| `name` | ○ | クラフトメニューに表示されるカテゴリ名 |
| `description` | ○ | カテゴリの説明文 |
| `skill_used` | ○ | 使用技能 |
| `nested_category_data` | ○ | このカテゴリに含める leaf recipe のIDの配列 |
| `difficulty` | ○ | カテゴリ全体の難易度。含まれる最も低いレシピの `difficulty` に合わせるのが一般的 |

## 重要な制約

### `nested_category_data` に `extend` は使えない

`nested_category_data` は CDDA 内部で `mandatory()` として読み込まれるため、`"extend"` や `"delete"` による部分修正ができない。

このため、**既存のバニラ nested_category にレシピを追加することは不可能**。必ず独自の nested_category を定義する必要がある。

### Leaf recipe の `category` / `subcategory` は固定

Leaf recipe 側の `category: "CC_*"` と `subcategory: "CSC_*_NESTED"` は常にこの値を使う。実際のクラフトメニュー上の位置は nested_category 側の `category` / `subcategory` で制御する。

## バリデーション

`check_mods.sh` 実行時、CDDA は `subcategory: "CSC_*_NESTED"` を持つすべてのレシピが、いずれかの nested_category の `nested_category_data` に含まれているか検証する。漏れがあると以下の debug warning が出力される：

```
recipe X is nested but isn't in a nested group. It will be impossible to path to by the player.
```

## 実装チェックリスト

- [ ] Leaf recipe の `category` は `"CC_*"`、`subcategory` は `"CSC_*_NESTED"` になっているか
- [ ] `type: "nested_category"` を定義し、leaf recipe のIDを `nested_category_data` に列挙しているか
- [ ] nested_category の `category` / `subcategory` は実際のクラフトメニューカテゴリ（`CC_CHEM` / `CSC_CHEM_MUTAGEN` 等）か
- [ ] `check_mods.sh` で debug warning が出ていないか

## バニラの実例

### 変異原レシピの親カテゴリ (`nested.json`)

```json
{
  "id": "nested_mutagen",
  "type": "nested_category",
  "activity_level": "LIGHT_EXERCISE",
  "category": "CC_CHEM",
  "subcategory": "CSC_CHEM_MUTAGEN",
  "name": "mutagens",
  "description": "Recipes related to synthesizing mutagenic substances.",
  "skill_used": "chemistry",
  "nested_category_data": [
    "purifier",
    "mutagen",
    "mutagen_rat",
    "mutagen_insect",
    "..."
  ],
  "difficulty": 7
}
```

### 対応する Leaf recipe (`mutagens.json`)

```json
{
  "type": "recipe",
  "result": "mutagen_insect",
  "category": "CC_*",
  "subcategory": "CSC_*_NESTED",
  "...": "..."
}
```
