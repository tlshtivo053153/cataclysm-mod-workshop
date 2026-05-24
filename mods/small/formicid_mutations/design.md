## Mod設計書: Formicid Mutations

### 仕様書から継承
- **目的**: CDDAにアリ型変異カテゴリ「FORMICID」を追加し、大顎・キチン装甲・蟻酸攻撃を持つ変異ツリーを提供する
- **スコープ**: 含むもの→変異カテゴリFORMICID、閾値変異、3つの変異（大顎→キチン甲羅→蟻酸腺）、ビタミン、変異原アイテム（液体＋IV）、変異原効果、変異原素材サンプル、レシピ（液体＋IV）。含まないもの→モンスター、職業
- **成功基準**: デバッグメニューで変異原をスポーンし、摂取/注射で変異が発現すること

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| mutation_category | FORMICID | 変異カテゴリ |
| mutation | THRESH_FORMICID | 閾値変異「Formic」 |
| mutation | FORM_MANDIBLES | 大顎。切断攻撃・装備制限 |
| mutation | FORM_CHITIN | キチン甲羅。防御力・仲間ボーナス |
| mutation | FORM_ACID_GLAND | 蟻酸腺。酸攻撃＋酸耐性 |
| vitamin | mutagen_formicid | 変異原プライマー |
| ITEM | mutagen_formicid | 飲用変異原 |
| ITEM | iv_mutagen_formicid | 注射用変異原プライマー |
| effect_type | mutagen_formicid | 変異中効果 |
| ITEM | formicid_sample | Formicid変異原サンプル |
| recipe | mutagen_formicid | 飲用変異原レシピ |
| recipe | iv_mutagen_formicid | 注射用プライマーレシピ |
| nested_category | nested_mutagen_formicid | Formicid変異原レシピグループ |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/mutations/mutation_category.json`
- [x] `external/cdda/data/json/mutations/mutations.json`
- [x] `external/cdda/data/json/vitamin.json`
- [x] `external/cdda/data/json/items/comestibles/mutagen.json`
- [x] `external/cdda/data/json/effects.json`

### ファイル構成
- modinfo.json
- data/mutation_category.json
- data/mutations.json
- data/vitamin.json
- data/mutagen_items.json
- data/mutagen_effects.json
- data/mutagen_ingredients.json
- data/mutagen_recipes.json

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作

### 変異詳細設計

**THRESH_FORMICID** — 閾値: 完全なアリ型生物への変異。valid:false, purifiable:false, threshold:true

**FORM_MANDIBLES** — 大顎。口装備制限。changes_toでFORM_CHITINへ誘導。
- points: 1, visibility: 9, ugliness: 8
- attacks: cut damage, chance 20%, amount 20
- restricts_gear: mouth

**FORM_CHITIN** — キチン甲羅。全身にcut:3/bash:2の防御。仲間が近くにいると快適さボーナス。
- points: 2, prereqs: FORM_MANDIBLES
- threshreq: THRESH_FORMICID
- comfort: npc_following condition

**FORM_ACID_GLAND** — 蟻酸腺。酸属性の近接攻撃＋全身酸耐性3。
- points: 2
- threshreq: THRESH_FORMICID
- attacks: acid damage, chance 20%, amount 8
- armor: acid 3 (全身)
