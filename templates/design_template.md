## Mod設計書: [mod名]

### 仕様書から継承
- **目的**: （仕様書の「背景・動機」と「追加/変更内容」を転記。小規模modで仕様書を省略した場合はここに直接記入）
- **スコープ**: （含むもの・含まないものを転記。小規模modで仕様書を省略した場合はここに直接記入）
- **成功基準**: （仕様書の成功基準を転記。小規模modで仕様書を省略した場合はここに直接記入）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）, [その他]

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| [item/monster/recipe等] | `mod_prefix_xxx` | 説明 |

### 参照ファイル（実在確認済み）
- [ ] `external/cdda/data/json/...` — copy-from先ID確認
- [ ] `external/cdda/data/json/...` — フラグ名確認
- [ ] `external/cdda/data/json/...` — マテリアルID確認
- [ ] `external/cdda/data/json/recipes/...` — activity_level の設定値確認（レシピを含む場合）

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json（レシピがある場合）

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### テスト手順
1. validate.shでJSON構文チェック（Level1）
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. CDDAを起動してLevel3確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作（フェーズ3以降で必須）
