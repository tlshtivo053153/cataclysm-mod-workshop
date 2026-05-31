## Mod設計書: scrap_bipod

### 目的
パイプとダクトテープで作る即席バイポッド（アンダーバレルガンモッド）を追加する。

### スコープ
- **含む:**
  - ガンモッド1種: `smb_scrap_bipod`（即席バイポッド）
  - レシピ1種: `smb_scrap_bipod` のクラフトレシピ
- **含まない:**
  - モンスター・シナリオ追加
  - 既存アイテムの改変
  - 上位グレードのバイポッド追加

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| GUNMOD | `smb_scrap_bipod` | 即席バイポッド、アンダーバレル |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/items/gunmod/` — バイポッド系gunmodのフォーマット・フラグ（`BIPOD`, `SLOW_WIELD`）確認

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### アイテム仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| id | `smb_scrap_bipod` | プレフィックス `smb_` |
| name | "scrap bipod" | |
| description | "A crude bipod made from scrap metal and duct tape. It attaches to the front of a long arm and provides some stability when aiming, though it's heavier and less effective than a proper bipod." | |
| weight | "700 g" | 即席品のため軽量寄り |
| volume | "500 ml" | |
| location | `underbarrel` | アンダーバレルスロット |
| mod_targets | `["rifle", "launcher", "smg", "shotgun", "crossbow"]` | 長物銃器全般 |
| handling_modifier | 6 | 中程度の取り回し改善 |
| flags | `BIPOD`, `SLOW_WIELD` | バイポッド効果＋構え遅延でバランス |
| material | `["steel"]` | パイプ＋ダクトテープ |
| min_skills | `[["weapon", 1]]` | 最低限の武器スキル要件 |

### レシピ仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| result | `smb_scrap_bipod` | |
| category | `CC_WEAPON` | |
| subcategory | `CSC_WEAPON_MODS` | |
| skill_used | `fabrication` | |
| skills_required | `[["gun", 1]]` | |
| difficulty | 1 | 簡易工作 |
| time | "15 m" | |
| autolearn | true | |
| components | pipe ×1, steel_chunk ×1, duct_tape ×50 | スクラップ素材 |

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - デバッグメニューで `smb_scrap_bipod` をスポーン
   - ライフル等にアンダーバレルとして取り付け可能か確認
   - クラフトメニューにレシピが表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] `smb_scrap_bipod` がデバッグメニューでスポーン可能
  - [ ] アンダーバレルスロットに取り付け可能
  - [ ] `BIPOD` フラグによる照準補正が機能する
  - [ ] クラフトメニューにレシピが表示される
