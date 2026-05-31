## Mod設計書: improvised_traps

### 目的
空き缶と紐の騒音警報器、廃材ワイヤーのスネア罠の2種の即席トラップを追加する。

### スコープ
- **含む:**
  - 罠2種: `tr_imp_trap_noise`（騒音警報器の罠実体）, `tr_imp_trap_cans_snare`（廃材ワイヤースネアの罠実体）
  - 罠設置キット2種: `imp_trap_noise_alarm`（騒音警報器, copy-from `light_snare_kit`）, `imp_trap_cans_snare`（廃材ワイヤースネア, copy-from `light_snare_kit`）
  - レシピ1種: `imp_trap_noise_alarm` のクラフトレシピ
- **含まない:**
  - `imp_trap_cans_snare` のレシピ（本modでは未定義、発見のみ）
  - モンスター・シナリオ追加
  - 上位グレードの罠追加

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| trap | `tr_imp_trap_noise` | 騒音警報器の罠実体 |
| trap | `tr_imp_trap_cans_snare` | 廃材ワイヤースネアの罠実体 |
| TOOL | `imp_trap_noise_alarm` | 騒音警報器の設置キット |
| TOOL | `imp_trap_cans_snare` | 廃材ワイヤースネアの設置キット |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/traps/` — 罠フォーマット確認（`action`, `avoidance`, `drops` 等）
- [ ] `external/cdda/data/json/items/tool/` — `light_snare_kit`（copy-from先）の実在確認
- [ ] `external/cdda/data/json/recipes/` — 罠設置キットのレシピフォーマット確認

### ファイル構成
- modinfo.json
- data/traps.json
- data/items.json
- data/recipes.json

### 実装順序
1. modinfo.json
2. data/traps.json
3. data/items.json
4. data/recipes.json

### 罠仕様

| フィールド | tr_imp_trap_noise | tr_imp_trap_cans_snare | 根拠 |
|---|---|---|---|
| id | `tr_imp_trap_noise` | `tr_imp_trap_cans_snare` | プレフィックス `tr_imp_` |
| name | "noise maker" | "scrap wire snare" | |
| color | light_gray | dark_gray | |
| symbol | `^` | `^` | CDDA罠標準 |
| visibility | 2 | 2 | 低視認性 |
| avoidance | 8 | 6 | ゾンビの回避率 |
| difficulty | 0 | 0 | 解除不可/設置のみ |
| action | `bubble` | `snare_light` | 騒音 / 軽量スネア |
| drops | `["imp_trap_noise_alarm"]` | `["imp_trap_cans_snare"]` | 罠解除時のドロップ |

### 設置キット仕様

| フィールド | imp_trap_noise_alarm | imp_trap_cans_snare | 根拠 |
|---|---|---|---|
| id | `imp_trap_noise_alarm` | `imp_trap_cans_snare` | プレフィックス `imp_` |
| copy-from | `light_snare_kit` | `light_snare_kit` | 軽量スネアキットを継承 |
| name | "noise alarm" | "scrap wire snare" | |
| weight | "1200 g" | "3200 g" | 金属部品のため重い |
| volume | "1500 ml" | "2500 ml" | |
| material | `["steel", "cotton"]` | `["steel"]` | 金属＋紐 / 金属のみ |
| trap | `tr_imp_trap_noise` | `tr_imp_trap_cans_snare` | |
| moves | 150 | 150 | 設置所要ターン |
| practice | 2 | 2 | トラップスキル練習値 |
| flags | `["SINGLE_USE"]` | `["SINGLE_USE"]` | 使い切り |
| needs_solid_neighbor | true | — | 騒音警報器のみ隣接壁必須 |

### レシピ仕様（noise alarm のみ）

| フィールド | 値 | 根拠 |
|---|---|---|
| result | `imp_trap_noise_alarm` | |
| category | `CC_OTHER` | |
| subcategory | `CSC_OTHER_TRAPS` | |
| skill_used | `fabrication` | |
| difficulty | 1 | 簡易工作 |
| time | "20 m" | |
| autolearn | true | |
| components | 空き缶(can_drink/can_food/can_medium) ×3, 紐類(string_36/string_6) ×1 | |

> **注意:** `imp_trap_cans_snare` にはレシピが定義されていない。本modでは当該アイテムは発見または他modのレシピからのみ入手可能。

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - デバッグメニューで `imp_trap_noise_alarm`, `imp_trap_cans_snare` をスポーン
   - 各キットを設置し罠が機能することを確認
   - クラフトメニューに noise alarm のレシピが表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] `imp_trap_noise_alarm` がデバッグメニューでスポーン可能、設置可能
  - [ ] `imp_trap_cans_snare` がデバッグメニューでスポーン可能、設置可能
  - [ ] noise alarm 設置時にトリガーで騒音発生（`bubble` アクション）
  - [ ] scrap wire snare 設置時にスネア効果（`snare_light` アクション）
  - [ ] noise alarm のクラフトレシピが表示される
  - [ ] cans_snare にはレシピが存在しないことを確認
