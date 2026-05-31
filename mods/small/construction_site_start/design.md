## Mod設計書: construction_site_start

### 目的
建設現場からゲーム開始する新規シナリオを追加する。

### スコープ
- **含む:**
  - シナリオ1種: `scenario_construction_site`（建設現場サバイバー）
  - スタート地点1種: `sloc_construction_site`（建設現場）
- **含まない:**
  - アイテム追加
  - レシピ追加
  - モンスター追加
  - 既存データの改変

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| scenario | `scenario_construction_site` | 建設現場スタートシナリオ |
| start_location | `sloc_construction_site` | 建設現場スタート地点 |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/scenarios/` — シナリオフォーマット確認
- [ ] `external/cdda/data/json/professions/` — `construction_worker`, `electrician`, `engineer_mech`, `mechanic` の実在確認
- [ ] `external/cdda/data/json/start_locations/` — スタート地点フォーマット確認

### ファイル構成
- modinfo.json
- data/scenario.json
- data/start_location.json

### 実装順序
1. modinfo.json
2. data/start_location.json
3. data/scenario.json

### シナリオ仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| id | `scenario_construction_site` | バニラ命名規則 `scenario_` に準拠 |
| name | "Construction Site Survivor" | |
| points | 0 | 標準難易度 |
| description | "You were working at a construction site when the Cataclysm hit.  Tools and materials are at hand, but the site is open to the outside." | |
| start_name | "Construction Site" | |
| allowed_locs | `["sloc_construction_site"]` | 自前のスタート地点のみ |
| professions | `construction_worker`, `electrician`, `engineer_mech`, `mechanic` | 現場作業に関連する職業 |
| flags | `CITY_START`, `LONE_START` | 都市開始・単独開始 |

### 開始地点仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| id | `sloc_construction_site` | バニラ命名規則 `sloc_` に準拠 |
| name | "Construction Site" | |
| terrain | `["construction_site"]` | 建設現場マップ地形 |
| flags | `["ALLOW_OUTSIDE"]` | 屋外開始許可 |

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認: 新規ゲーム → シナリオ選択で "Construction Site Survivor" が表示されること、開始地点が建設現場であること

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作
  - [ ] シナリオ選択画面に "Construction Site Survivor" が表示される
  - [ ] 指定職業 (construction_worker, electrician, engineer_mech, mechanic) が選択可能
  - [ ] 開始地点が建設現場である
