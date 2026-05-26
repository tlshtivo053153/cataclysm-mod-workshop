## Mod設計書: scrap_striker mod

### 目的
- バニラの `BATONS` 武器カテゴリ（パイプ、バット、バール等）に特化した新規格闘スタイル「Scrap Striker」を追加する
- 廃材や即席武器で戦うサバイバー向けの、粗野で破壊力重視の格闘スタイル

### スコープ
- 含むもの:
  - 格闘スタイル1種: `style_scrap_striker`
  - 常時バフ1種: `buff_scrap_striker_static`（インライン、鈍器ダメージ+10%）
  - テクニック2種: `tec_scrap_striker_smash`（粉砕打）、`tec_scrap_striker_backhand`（連続打）
- 含まないもの:
  - アイテム・レシピ追加
  - モンスター追加
  - NPC・シナリオ変更
  - 既存データの改変

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 参照ファイル（external/cdda/）
- [x] data/json/martialarts.json — bojutsu (BATONS weapon_category, strictly_melee, primary_skill: bashing) を構造リファレンスとして確認
- [x] data/json/techniques.json — tec_bojutsu系テクニックの weapon-only 構造を確認（attack_vectors: ["vector_null"], skill_requirements: "melee", mult_bonuses配列）
- [x] data/json/weapon_categories.json — BATONS カテゴリ定義確認（prof_batons_familiar/pro/pro_master）
- [x] doc/JSON/MARTIALART_JSON.md — 全フィールドの有効性確認

### ファイル構成
```
mods/small/scrap_striker/
├── design.md           ← この設計書
├── modinfo.json
└── data/
    ├── martialarts.json
    └── techniques.json
```

### 格闘スタイル仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| id | `style_scrap_striker` | |
| name | "Scrap Striker" | |
| priority | 1 | 通常のプレイアブルスタイル |
| learn_difficulty | 3 | 即席スタイルに適した難易度 |
| primary_skill | `bashing` | 鈍器マスタリー |
| strictly_melee | true | 武器必須 |
| arm_block | 1 | unarmed 1で腕ブロック（バニラの慣例: 素手スキル紐付け） |
| autolearn | `[["bashing", 4]]` | bashing 4で自動習得 |
| weapon_category | `["BATONS"]` | baton, bat, crowbar, pipe, nail bat, PR24, shillelagh等 |

### バフ仕様 (buff_scrap_striker_static)

| フィールド | 値 |
|---|---|
| id | `buff_scrap_striker_static` |
| name | "Heavy Grip" |
| description | "You put your full weight behind every swing.\n\n+10% bash damage." |
| melee_allowed | true |
| mult_bonuses | `[{ "stat": "damage", "type": "bash", "scale": 1.1 }]` |

### テクニック仕様

**tec_scrap_striker_smash (Crushing Smash):**
- ダメージ+25% / 速度-20%
- weapon-only (attack_vectors: ["vector_null"])
- スキル要件なし（常時発動可能）

**tec_scrap_striker_backhand (Quick Backswing):**
- 速度+30% / ダメージ-20%
- weapon-only (attack_vectors: ["vector_null"])
- skill_requirements: melee 3以上

### バランス検証
- ダメージ寄りのスタイル（bojutsuの技術的スタイルより破壊力重視、barbaranの無制限より制限的）
- バフのダメージ+10%は他武器スタイルの範囲内
- BATONSカテゴリのみに制限することで汎用性を抑制

### テスト手順
1. CDDA起動、scrap_striker mod有効化
2. デバッグメニューでバット/パイプ/バールをスポーン
3. デバッグ: bashingスキルを4以上に（autolearn発動）
4. `_`キーでScrap Strikerスタイルに切り替え
5. 近接戦闘: smash / backhandテクニックのメッセージ表示を確認
6. バフ効果（bashダメージボーナス）を@ステータスで確認

### 完了条件
- [ ] Level1: JSON構文OK（validate.sh パス）
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] スタイルが martial arts メニューに表示される
  - [ ] テクニックが BATONS 武器で発動する
  - [ ] バフのダメージボーナスが適用される
