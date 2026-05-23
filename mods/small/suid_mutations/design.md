## Mod設計書: SUID Mutations

### 仕様書から継承
- **目的**: CDDAにイノシシ/ブタ系変異カテゴリ「SUID」を追加し、頑丈な突進攻撃＋探知能力を持つ変異ツリーを提供する
- **スコープ**: 含むもの→変異カテゴリSUID、閾値変異、3つの非閾値変異、ビタミン、変異原アイテム（液体＋IV）、変異原効果。含まないもの→レシピ、モンスター、職業
- **成功基準**: デバッグメニューで変異原をスポーンし、摂取/注射で変異が発現すること

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| mutation_category | SUID | 変異カテゴリ |
| mutation | THRESH_SUID | 閾値変異「Swine」 |
| mutation | SUID_SNOUT | 鼻先変異。嗅覚強化・腐肉食可能・ugliness |
| mutation | SUID_TUSKS | 牙攻撃。貫通ダメージ・威圧ボーナス |
| mutation | SUID_HIDE | 厚皮。bash/cut 防御 |
| vitamin | mutagen_suid | 変異原プライマー |
| ITEM | mutagen_suid | 飲用変異原 |
| ITEM | iv_mutagen_suid | 注射用変異原プライマー |
| effect_type | mutagen_suid | 変異中効果 |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/mutations/mutation_category.json` — カテゴリ構造確認
- [x] `external/cdda/data/json/mutations/mutations.json` — threshold mutationsパターン確認
- [x] `external/cdda/data/json/vitamin.json` — mutagen_* ビタミン構造確認
- [x] `external/cdda/data/json/items/comestibles/mutagen.json` — 変異原アイテム構造確認
- [x] `external/cdda/data/json/effects.json` — mutagen_* 効果構造確認

### ファイル構成
- modinfo.json
- data/mutation_category.json
- data/mutations.json
- data/vitamin.json
- data/mutagen_items.json
- data/mutagen_effects.json

### 実装順序
1. modinfo.json
2. data/mutation_category.json
3. data/mutations.json
4. data/vitamin.json
5. data/mutagen_items.json
6. data/mutagen_effects.json

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認（デバッグメニューでmutagen_suid / iv_mutagen_suidをスポーンし変異を確認）

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作

### 変異詳細設計

**THRESH_SUID** — 閾値: 豚/猪の本質を受け入れる。valid:false, purifiable:false, threshold:true

**SUID_SNOUT** — 鼻先が平たく広がり豚の鼻先になる。嗅覚が著しく強化されるが外見は醜くなる。腐敗した食料も消化可能。
- points: 1, visibility: 9, ugliness: 7
- flags: ["STRONGSTOMACH"] (腐敗食料のペナルティ軽減 = SAPROVOREに類似)
- social_modifiers: { "intimidate": -3 }
- category: ["SUID"]

**SUID_TUSKS** — 口から鋭い牙が突き出る。噛みつき攻撃に刺突ダメージ追加。威圧的だが装備制限あり。
- points: 1, visibility: 8, ugliness: 10
- prereqs: ["SUID_SNOUT"]
- attacks: 貫通ダメージ（stab）、確率20%、ダメージ16
- restricts_gear: ["mouth"]
- social_modifiers: { "intimidate": 4 }
- category: ["SUID"], threshreq: ["THRESH_SUID"]

**SUID_HIDE** — 厚い皮下組織と強靭な皮。bash/cutに高い防御力。やや動きにくくなる。
- points: 2, visibility: 6, ugliness: 4
- prereqs: ["SUID_SNOUT"]
- armor: bash: 3, cut: 3 (全身)
- encumbrance: torso+head+arms+legsに少し
- category: ["SUID"], threshreq: ["THRESH_SUID"]
