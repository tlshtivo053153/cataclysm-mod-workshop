## Mod設計書: Makeshift Wire Saw

### 目的
スクラップ素材から作れる簡易のこぎりを追加。序盤の木工作業を補助。

### スコープ
- **含む:** 新規TOOLアイテム1種、製作レシピ1種
- **含まない:** 専用耐久度システム、電動化、収納ケース

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 参照ファイル（external/cdda/）
- `data/json/items/generic.json` → `makeshift_hammer`（TOOL構造参考）
- `data/json/recipes/recipe_others.json` → 製作レシピ参考

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### テスト手順
1. validate.shでJSON構文チェック
2. link_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認
4. CDDAを起動してLevel3確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作（フェーズ3以降で必須）
