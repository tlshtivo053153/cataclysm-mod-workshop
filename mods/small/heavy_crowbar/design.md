## Mod設計書: heavy_crowbar mod

### 目的
- バニラの `crowbar` を継承した強化版バールを追加する
- フェーズ1のJSONフォーマット・copy-from習得を目的とした最小構成mod

### スコープ
- 含むもの:
  - アイテム1種: `hcb_reinforced_crowbar`（強化バール）
  - レシピ1種: `hcb_reinforced_crowbar` のクラフトレシピ
- 含まないもの:
  - モンスター追加
  - NPC・シナリオ変更
  - 既存アイテムの改変

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 参照ファイル（external/cdda/）
- [x] data/json/items/tool/entry_tools.json（crowbar の数値確認済み）
  - crowbar: bash 19, weight "1456 g", volume "520 ml", price "26 USD"
  - heavy_crowbar（バニラ）: bash 45, weight "6201 g"
  - → hcb_reinforced_crowbar の目標値: bash 28, weight "2200 g"（crowbarの+50%以内）

### ファイル構成
```
mods/small/heavy_crowbar/
├── design.md           ← この設計書
├── modinfo.json
└── data/
    ├── items.json
    └── recipes.json
```

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### アイテム仕様

| フィールド | 値 | 根拠 |
|---|---|---|
| id | `hcb_reinforced_crowbar` | プレフィックス `hcb_` |
| copy-from | `crowbar` | バニラIDが存在することを確認済み |
| name | "reinforced crowbar" | |
| description | 金属バンドで補強された頑丈なバール | |
| weight | "2200 g" | crowbar(1456g)の+50%以内 |
| melee_damage.bash | 28 | crowbar(19)の+47%（±50%以内） |

### レシピ仕様

| フィールド | 値 |
|---|---|
| result | `hcb_reinforced_crowbar` |
| category | `CC_WEAPON` |
| subcategory | `CSC_WEAPON_BASHING` |
| skill_used | `fabrication` |
| difficulty | 3 |
| time | `45 m` |
| autolearn | false |
| components | crowbar ×1, steel_chunk ×2, duct_tape ×1 |

### テスト手順
1. CDDAを起動してheavy_crowbar modを有効化
2. デバッグメニュー（`~`キー）でアイテムをスポーン: `hcb_reinforced_crowbar`
3. アイテムが表示され装備できることを確認
4. クラフトメニューでレシピが表示されることを確認（fabrication スキル必要）

### 完了条件
- [x] Level1: JSON構文OK（validate.sh パス）
- [x] Level2: 起動OK（エラーなし）
- [x] Level3: 意図通り動作
  - [x] `hcb_reinforced_crowbar` がデバッグメニューでスポーン可能
  - [x] クラフトメニューにレシピが表示される
  - [x] アイテムを装備/使用してもクラッシュしない
  - [x] ステータスが設計値通り（bash 28, weight 2200g）
