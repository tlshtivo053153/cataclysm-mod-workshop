## Mod設計書: combat_stim

### 仕様書から継承
- **目的**: 単体 `type: "enchantment"` を effect_type から ID 参照する未実証パターンの検証
- **スコープ**: enchantment / effect_type / 医薬品 / レシピのみ。モンスター・マップ・NPC は含まない
- **成功基準**: `cst_combat_stim` 使用で `cst_effect_stim` が付与され、enchantment の補正が反映される

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| enchantment | `cst_ench_stim` | 興奮剤の戦闘補正（MELEE_DAMAGE +2 / ATTACK_SPEED -10 / PAIN ×-0.5） |
| effect_type | `cst_effect_stim` | 興奮状態。`enchantments: [ "cst_ench_stim" ]` で ID 参照 |
| ITEM (COMESTIBLE) | `cst_combat_stim` | 戦闘興奮剤（copy-from: `adrenaline_injector`） |
| recipe | `cst_combat_stim` | 化学レシピ（adrenaline_injector + caffeine + chem_ethanol） |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/items/comestibles/med.json` — `adrenaline_injector`（55行目, COMESTIBLE/consume_drug）
- [x] `external/cdda/data/json/items/comestibles/med.json` — `caffeine`（287行目, レシピ素材）
- [x] `external/cdda/data/json/recipes/recipe_medsandchemicals.json` — adrenaline_injector レシピ（`activity_level: "LIGHT_EXERCISE"`, CC_CHEM / CSC_CHEM_DRUGS）
- [x] `external/cdda/data/json/effects.json` — `pkill2`, `adrenaline`（effect_type の書式確認）
- [x] `external/cdda/data/json/effects.json` — `mech_recon_vision`（effect_type → 単体 enchantment ID 参照の実例）
- [x] `external/cdda/data/json/enchantments.json` — `THERMAL_VISION_GOOD_PASSIVE`（condition: ALWAYS / values の書式）
- [x] `external/cdda/data/mods/Aftershock/items/item_enchants.json` — `ench_cold_armor`（単体 enchantment の name / description 書式）
- [x] `rules/patterns/enchantment.md` — value セマンティクス（ATTACK_SPEED は負値で高速化、PAIN は multiply）

### ファイル構成
```
mods/small/combat_stim/
├── spec.md
├── design.md
├── modinfo.json
└── data/
    ├── enchantments.json
    ├── effects.json
    ├── items.json
    └── recipes.json
```

### 設計詳細

| フィールド | 値 | 根拠 |
|---|---|---|
| copy-from | `adrenaline_injector` | 医薬品・consume_drug の書式継承 |
| name | `{ "str_sp": "combat stimulant injector" }` | CORE.md: COMESTIBLE は str_sp |
| weight / volume | "14 g" / "12 ml" | 元アイテム（12 g / 10 ml）の +20% 以内 |
| stim | 40 | 元アイテム 29 より強力な興奮作用 |
| use_action | consume_drug / effects: cst_effect_stim (5 m) | 既存 adrenaline の effects 書式に準拠 |
| recipe difficulty | 4 | base adrenaline レシピ（6）より入手しやすく、序盤の選択肢に |

### 実装順序
1. modinfo.json
2. data/enchantments.json
3. data/effects.json
4. data/items.json
5. data/recipes.json

### テスト手順
1. `bash scripts/validate.sh mods/small/combat_stim/`（Level1）
2. `bash scripts/place_mod_for_test.sh --link mods/small/combat_stim/`
3. `bash scripts/check_mods.sh --check-errors combat_stim`（Level2）
4. CDDA 起動 → デバッグメニューで `cst_combat_stim` をスポーン → 使用して効果とキャラクターシートの数値変化を確認（Level3）

### 完了条件
- [x] Level1: JSON構文OK
- [x] Level2: 起動OK（ERROR なし）
- [ ] Level3: 意図通り動作（効果付与・enchantment 反映）— **未実行（手動確認待ち）**
