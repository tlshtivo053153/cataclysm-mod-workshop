## Mod設計書: Turtle Mutations

### 仕様書から継承
- **目的**: CDDAにカメ型変異カテゴリ「TURTLE」を追加し、甲羅による高い防御力と水生適性を持つ変異ツリーを提供する
- **スコープ**: 含むもの→変異カテゴリTURTLE、閾値変異、3つの変異（甲羅2段階＋くちばし）、ビタミン、変異原アイテム（液体＋IV）、変異原効果。含まないもの→レシピ、モンスター、職業
- **成功基準**: デバッグメニューで変異原をスポーンし、摂取/注射で変異が発現すること

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| mutation_category | TURTLE | 変異カテゴリ |
| mutation | THRESH_TURTLE | 閾値変異「Chelonian」 |
| mutation | TURTLE_SHELL_PLATES | 甲羅板。軽度防御・速度低下 |
| mutation | TURTLE_SHELL | 完全甲羅。高防御・装備制限 |
| mutation | TURTLE_BEAK | くちばし攻撃 |
| vitamin | mutagen_turtle | 変異原プライマー |
| ITEM | mutagen_turtle | 飲用変異原 |
| ITEM | iv_mutagen_turtle | 注射用変異原プライマー |
| effect_type | mutagen_turtle | 変異中効果 |

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

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
