## Mod設計書: alt_recipes（ほぐし火口の代替レシピ）

### 仕様書から継承
- **目的**: バニラ既存 `tinder` への第4レシピ（`id_suffix: scrap_alt`）を追加し、紙系＋木片系の手持ち端材でも火口を作れるようにする。B-3「純粋レシピ追加」で新規ID 0の最易パターン。
- **スコープ**:
  - 含むもの：既存品 `tinder` への代替レシピ1件のみ
  - 含まないもの：新規ITEM・新casing・新effect・item_group注入・nested_category定義・バランス調整（Step 9）・Level3動作確認（Step 8）
- **成功基準**: Level1（`bash scripts/validate.sh mods/small/alt_recipes/` 通過）＋Level2（`bash scripts/check_mods.sh --isolated --check-errors alt_recipes`、終了コード0＋debug.log ERRORなし）通過。Level3（Step 8）・Step 9は対象外として未実施。

### 小規模判定（Step 1・2省略根拠）
- [x] 新規ID 0個 ≤5（recipeはresult `tinder` 参照で新IDなし。`id_suffix: scrap_alt` はrecipe内部識別でゲームIDに数えない。modinfo.json除く）
- [x] 既存タイプのみ（`type: recipe` の通常定義。`copy-from` ではなく新規entryだが既存typeの新entryに限り許容。新規 `type` 定義なし）
- [x] 既存システム拡張のみ（火口クラフトの代替手段追加のみ。新システム・mapgen・NPC logicなし）
- [x] 同カテゴリ派生（既存 `tinder` レシピ3件と同一 category `CC_OTHER` / subcategory `CSC_OTHER_MATERIALS` / skill `survival` / difficulty 1 の明確な派生）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| recipe | （result=`tinder`, `id_suffix: scrap_alt`） | 紙系＋木片系の代替火口レシピ |

新規ID数: 0。衝突確認：`grep -rn '"scrap_alt"' external/cdda/data/json/ mods/` が0件、`grep -r '"alt_recipes"' external/cdda/data/json/ mods/` が0件（実装前に再確認済み）。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/recipes/recipe_ammo.json` — `tinder` 3件併存（無印＋`softer`＋`softest`）、`id_suffix` による重複回避の前例。代表1件（無印）が `LIGHT_EXERCISE` / difficulty 1 / `survival` / `CC_OTHER` / `CSC_OTHER_MATERIALS` / `autolearn: true`
- [x] `external/cdda/data/json/items/ammo.json:1601` — `tinder`（result先ID確認）
- [x] `external/cdda/data/json/items/generic.json:1638` — `paper`（成分ID確認）
- [x] `external/cdda/data/json/items/comestibles/other.json:447` — `cardboard`（成分ID確認。tinder既存成分として実証済み）
- [x] `external/cdda/data/json/items/resources/wood.json:22` — `splinter`（成分ID確認）
- [x] `external/cdda/data/json/items/generic.json:2263` — `pinecone`（成分ID確認。tinder既存成分として実証済み）
- [x] `external/cdda/data/json/tool_qualities.json:4` — `CUT`（quality ID確認。softer準拠でlevel 1）
- [x] `external/cdda/data/json/skills.json:280` — `survival`（skill ID確認）
- [x] `external/cdda/data/json/recipes/recipe_ammo.json` — activity_level の設定値確認（参照3件すべて `LIGHT_EXERCISE`。0.I必須のため自レシピも同値）

### レシピ仕様
| フィールド | 値 | 根拠 |
|---|---|---|
| type | `recipe` | 通常定義（B-3準拠。copy-fromなし） |
| result | `tinder` | バニラ既存品への代替レシピ |
| id_suffix | `scrap_alt` | 既存 `softer` / `softest` と重ならない一意名 |
| category | `CC_OTHER` | 参照3件準拠 |
| subcategory | `CSC_OTHER_MATERIALS` | 参照3件準拠。`CSC_*_NESTED` を使わないため `nested_category` 定義不要 |
| skill_used | `survival` | 参照3件準拠 |
| difficulty | 1 | 参照3件準拠 |
| time | `2 m` | 既存3件 `1 m` に対し+1 mのコスト増（時間短縮によるバランス破壊を避ける意図的加算） |
| activity_level | `LIGHT_EXERCISE` | 0.I必須。参照3件準拠 |
| autolearn | `true` | 参照3件準拠（`book_learn` 方式は不採用） |
| qualities | `[{id: CUT, level: 1}]` | `softer` 準拠（無印はCUT 2、softestはqualitiesなしのため最小要件の前例はsofter） |
| components | `[[[paper, 3], [cardboard, 1]], [[splinter, 2], [pinecone, 2]]]` | 既存3件と重ならない組合せ。`paper 3` は既存 `paper 5` より少ないが第2要素（`splinter 2`）とのAND結合で総コスト同等以上。既存より明確に安い単一成分のみのレシピは境界外 |
| charges | （定義しない） | tinder参照3件にchargesなしのため前例一致 |
| tools | （定義しない） | softest前例準拠（toolsなしで通過実証済み） |

### ファイル構成
- modinfo.json
- data/items.json（本modでは該当なし。新規ITEMを作らないため作成しない）
- data/recipes.json（レシピがある場合。本modの本体1件）

### 実装順序
1. modinfo.json
2. data/items.json（本modではスキップ。新規ITEMなしのため）
3. data/recipes.json

### テスト手順
1. validate.shでJSON構文チェック（Level1。各編集後に実行：`bash scripts/validate.sh mods/small/alt_recipes/`）
2. place_mod_for_test.shでCDDAに配置（`bash scripts/place_mod_for_test.sh mods/small/alt_recipes/`＋`readlink` で鮮度確認）
3. check_mods.shでmod読み込み確認（Level2：`bash scripts/check_mods.sh --isolated --check-errors alt_recipes`、終了コード0＋debug.log ERRORなし）
4. CDDAを起動してLevel3確認 — **対象外（実施しない。Level定義の正本は `rules/verification.md`）**

### 完了条件
- [x] Level1: JSON構文OK（`validate.sh` 通過。`OK: data/recipes.json`＋`OK: modinfo.json`、`All files passed`、終了コード0）
- [x] Level2: 起動OK（エラーなし。`check_mods.sh --isolated --check-errors alt_recipes` 終了コード0＋ERROR 0。log `logs/check_alt_recipes_20260920_031127.log`）
- [ ] Level3: 対象外として未実施（必須・手動確認だが本計画の範囲外。Level定義の正本は `rules/verification.md`）
- [ ] 新規IDが0個に収まり、小規模条件を満たす（上記「小規模判定」4件）
- [ ] Step 9（バランス調整）は未実施（対象外として明記）
- [ ] △群（PROMPT.md §7.3、C-2含む）は未着手（対象外として明記。本modと無関係）

### Step 4整合性再確認記録
- 2026-09-19実施。すべて一致、実装続行可。
- `grep -c '"result": "tinder"' recipe_ammo.json` → 3（併存実証）。OK
- 代表1件（無印）→ `LIGHT_EXERCISE` / difficulty 1 / `survival` / `CC_OTHER` / `CSC_OTHER_MATERIALS` / `autolearn: true`。OK
- `id_suffix: softer` / `softest` 実在、自レシピ `scrap_alt` と重ならず（`grep -rn '"scrap_alt"'` 0件）。OK
- `tinder`（ammo.json:1601）、`paper`（generic.json:1638）、`splinter`（wood.json:22）、`cardboard`（other.json:447）、`pinecone`（generic.json:2263）、`CUT`（tool_qualities.json:4）、`survival`（skills.json:280）すべて実在。OK
- `grep -r '"alt_recipes"' external/cdda/data/json/ mods/` → 0件（mod id衝突なし）。`ls mods/small/alt_recipes` 不在（新規作成可）。OK

### 陽性対照記録（T6b/T6d。一時modで実行し本体は汚さない。いずれも撤去済み）
- T6b 未知成分：成分1件を `__no_such_item__` に置換した一時mod `alt_fault_tmp` → `check_mods.sh` 終了コード2＋debug.log ERROR 2行（`__no_such_item__ ... is not a valid item template`）。検出成立。注：planの期待値 `exit 4`（`check_mods.sh:287-299` のERROR検査ブロック）に対し実測は `exit 2`（`:275-282` でエンジン異常終了時に先にreturn）。不正検出（非0＋ERROR）自体は成立。
- T6d `activity_level` 除去：一時mod `alt_noact_tmp`（`activity_level` フィールドなし）→ `check_mods.sh` 終了コード2＋debug.log ERROR 2116行（2回再現。いずれも `logs/check_alt_noact_tmp_20260920_031000.log` / `..._031211.log`）。対して本体は2回とも終了コード0＋ERROR 0（`logs/check_alt_recipes_20260920_030459.log` / `..._031127.log`）。log内に `recipe` 言及0件のため帰属は差分実証（除去で確定反転）による。`activity_level` がLevel2必須であることの陽性対照として成立。
