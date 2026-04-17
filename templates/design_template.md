## Mod設計書: [mod名]

### 目的
- 何を追加/変更するか

### スコープ
- 含むもの
- 含まないもの（重要）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）, [その他]

### 参照ファイル（external/cdda/）
- [ ] data/json/[参照ファイル]

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json（レシピがある場合）

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### テスト手順
1. CDDAを起動してmodを有効化
2. デバッグメニュー（`~`キー）でアイテムをスポーンして確認
3. クラフトメニューでレシピが表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作（フェーズ3以降で必須）