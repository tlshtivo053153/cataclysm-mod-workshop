## Mod設計書: improvised_emag

### 目的
標準STANAG 30連マガジン2つを切断・溶接して作る45連拡張マガジンを追加する。

### スコープ
- **含む:**
  - マガジン1種: `iem_stanag45`（即席45連STANAG拡張マガジン, copy-from `stanag30`）
  - レシピ1種: `iem_stanag45` のクラフトレシピ
- **含まない:**
  - 他口径バリエーション
  - ドラムマガジン
  - モンスター・シナリオ追加

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| MAGAZINE | `iem_stanag45` | 即席45連STANAG拡張マガジン |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/items/magazine/` — `stanag30` のベースステータス確認（weight, volume, pocket_data, reload_time, mag_jam_mult）

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
| id | `iem_stanag45` | プレフィックス `iem_` |
| copy-from | `stanag30` | バニラSTANAG 30連を継承 |
| name | "improvised 45-round STANAG extended magazine" | |
| description | "Two STANAG magazines cut and welded together into a field-expedient extended magazine.  Holds 45 rounds but is bulky and slower to reload." | |
| weight | "330 g" | stanag30(約250g)より重い |
| volume | "500 ml" | |
| ammo_restriction | 223: 45, 300blk: 30 | 拡張+30%、.300blkは制限 |
| reload_time | 130 | stanag30(100)より遅い |
| mag_jam_mult | 2 | 即席品の信頼性低下 |
| flags | `MAG_BULKY` | かさばるマガジン |

### レシピ仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| result | `iem_stanag45` | |
| category | `CC_WEAPON` | |
| subcategory | `CSC_WEAPON_MAGAZINES` | |
| skill_used | `fabrication` | |
| skills_required | `["gun", 2]` | |
| difficulty | 3 | 中程度の工作難易度 |
| time | "45 m" | |
| autolearn | true | |
| tools | small_repairkit ×10 or large_repairkit ×5 | |
| qualities | SAW_M ×1, HAMMER ×1, SCREW_FINE ×1 | |
| using | `[["welding_standard", 5]]` | |
| components | stanag30 ×2, duct_tape ×40, spring ×1 | 2つのマガジンを切断溶接 |

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - デバッグメニューで `iem_stanag45` をスポーン
   - 5.56mm対応銃器に装填し45発入ることを確認
   - クラフトメニューにレシピが表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] `iem_stanag45` がデバッグメニューでスポーン可能
  - [ ] 223弾薬を45発装填可能
  - [ ] 300blk弾薬を30発装填可能
  - [ ] reload_time 130、mag_jam_mult 2 が適用されている
  - [ ] クラフトメニューにレシピが表示される
