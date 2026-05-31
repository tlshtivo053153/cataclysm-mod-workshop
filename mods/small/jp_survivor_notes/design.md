## Mod設計書: jp_survivor_notes

### 目的
日本語の生存者メモ・落書きスニペットをゲームに追加し、日本語話者の没入感を高める。

### スコープ
- **含む:**
  - ノートスニペット12種（`jpn_note_1`〜`jpn_note_12`, category: `note`）
  - グラフィティスニペット6種（`jpn_graffiti_1`〜`jpn_graffiti_6`, category: `general_graffiti_snippets`）
  - 合計18件の日本語テキストスニペット
- **含まない:**
  - アイテム追加（ノートアイテム自体はバニラの `note` カテゴリに自動統合）
  - レシピ追加
  - モンスター・シナリオ変更

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| snippet | `jpn_note_1`〜`jpn_note_12` | 生存者の手書きメモ・日記断片・走り書き（カテゴリ: note） |
| snippet | `jpn_graffiti_1`〜`jpn_graffiti_6` | 避難所や建物の壁の落書き（カテゴリ: general_graffiti_snippets） |

### スニペットカテゴリとテーマ

| カテゴリ | 件数 | テーマ・内容 |
|---|---|---|
| `note` | 12件 | 生存者の日記・メモ断片（絶望、希望、孤独、移動の記録、他者への伝言） |
| `general_graffiti_snippets` | 6件 | 壁や看板の落書き（生存宣言、警告、励まし、皮肉） |

### 参照ファイル（external/cdda/） — 要確認
- [ ] `external/cdda/data/json/snippets/` — スニペットフォーマット確認（`type: "snippet"`, `category`, `text` 配列構造）
- [ ] `external/cdda/doc/JSON/SNIPPET_JSON.md` — スニペット仕様書

### ファイル構成
- modinfo.json
- data/snippets.json

### 実装順序
1. modinfo.json
2. data/snippets.json

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認:
   - ノートアイテム（`note` カテゴリ）を収集し、日本語テキストがランダム表示されることを確認
   - 壁の落書き（`general_graffiti_snippets`）が避難所などにランダム表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: スニペットがゲーム内でランダム表示されることを確認
  - [ ] ノートスニペット（`jpn_note_1`〜`12`）のいずれかが表示される
  - [ ] グラフィティスニペット（`jpn_graffiti_1`〜`6`）のいずれかが表示される
