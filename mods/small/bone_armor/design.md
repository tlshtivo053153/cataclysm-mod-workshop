## Mod設計書: bone_armor

### 仕様書から継承
- **目的**: base に一式が存在しない骨防具を追加し、ARMOR subtype の実装ノウハウを蓄積する
- **スコープ**: 胴・頭・腕の骨防具3点とレシピ3件のみ
- **成功基準**: スポーン・装備・クラフトが正常動作し、Level2 を通過する

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| ITEM (ARMOR) | `bna_bone_cuirass` | 骨の胴鎧（copy-from: `armor_chitin`） |
| ITEM (ARMOR) | `bna_bone_helmet` | 骨の兜（copy-from: `helmet_chitin`） |
| ITEM (ARMOR) | `bna_bone_armguards` | 骨の腕甲（copy-from: `armguard_chitin`） |
| recipe | `bna_bone_cuirass` | tailor 4 / 2 h |
| recipe | `bna_bone_helmet` | tailor 3 / 1 h |
| recipe | `bna_bone_armguards` | tailor 2 / 45 m |

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/items/armor/suits_protection.json` — `armor_chitin`（34行目, ARMOR / item-level material + material_thickness）
- [x] `external/cdda/data/json/items/armor/helmets.json` — `helmet_chitin`（768行目, material_thickness 4）
- [x] `external/cdda/data/json/items/armor/arms_armor.json` — `armguard_chitin`（106行目）
- [x] `external/cdda/data/json/materials.json` — `bone`（254行目）/ `leather`（1338行目）
- [x] `external/cdda/data/json/items/resources/bone.json` — `bone` アイテム（290 g）
- [x] `external/cdda/data/json/recipes/armor/arms.json` — 防具レシピ書式（`activity_level`, CC_ARMOR / CSC_ARMOR_ARMS）
- [x] `external/cdda/data/json/recipes/recipe_others.json` — `cordage_short` の使用例（book_binder レシピ）
- [x] サブカテゴリ実在確認 — `CSC_ARMOR_TORSO` / `CSC_ARMOR_HEAD` / `CSC_ARMOR_ARMS`

### ファイル構成
```
mods/small/bone_armor/
├── spec.md
├── design.md
├── modinfo.json
└── data/
    ├── items.json
    └── recipes.json
```

### 設計詳細

| アイテム | copy-from | material | weight | material_thickness | 備考 |
|---|---|---|---|---|---|
| bna_bone_cuirass | armor_chitin | bone + leather | 3200 g | 5 | chitin(2632 g/厚4)より重く硬い |
| bna_bone_helmet | helmet_chitin | bone + leather | 1700 g | 4 | WATERPROOF を削除（骨は非防水） |
| bna_bone_armguards | armguard_chitin | bone + leather | 650 g | 4 | WATER_FRIENDLY を削除 |

- `armor` 配列は基本コピー元から継承（chitin 系は item-level `material` + `material_thickness` 方式のため、material 差し替えのみで骨の防護値になる）。ただし `bna_bone_cuirass` のみ意図的に `covers: [torso]` で上書きし、親 `armor_chitin` の脚（leg_l/leg_r）防護を落としている（cuirass=胴鎧のため）
- `name` は `{ "str": ... }`（ARMOR の base 慣習に合わせる）。ただし `cuirass`（不規則複数）・`pair of ...` は `str_pl` 必須（実データ通り）

### レシピ設計

| レシピ | skill | difficulty | time | components | activity_level |
|---|---|---|---|---|---|
| cuirass | tailor | 4 | 2 h | bone ×10, leather ×4, cordage_short ×6 | LIGHT_EXERCISE |
| helmet | tailor | 3 | 1 h | bone ×5, leather ×2, cordage_short ×3 | LIGHT_EXERCISE |
| armguards | tailor | 2 | 45 m | bone ×4, leather ×2, cordage_short ×2 | LIGHT_EXERCISE |

- `autolearn: true`（原始的な骨加工はサバイバル技能として自然に習得）
- `qualities`: CUT 1 / LEATHER_AWL 1

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### テスト手順
1. `bash scripts/validate.sh mods/small/bone_armor/`（Level1）
2. `bash scripts/place_mod_for_test.sh --link mods/small/bone_armor/`
3. `bash scripts/check_mods.sh --check-errors bone_armor`（Level2）
4. CDDA 起動 → デバッグメニューで3点をスポーン・装備、クラフトメニュー表示を確認（Level3）

### 完了条件
- [x] Level1: JSON構文OK
- [x] Level2: 起動OK（ERROR なし）
- [ ] Level3: 意図通り動作（装備・クラフト）— **未実行（手動確認待ち）**
