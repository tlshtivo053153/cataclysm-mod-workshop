## Mod設計書: scrap_9mm（スクラップ9mm装弾）

### 仕様書から継承
- **目的**: 鉛スクラップと少量火薬で手詰めした粗悪9mm弾を追加する。威力・精度は劣るが、`pipe_pistol`（使用弾薬種 `9mm`）と互換があり、序盤の弾薬枯渇を緩和する。リロード済み弾（reloaded）の下位互換。GUN（pipe_pistol）・MAGAZINE（improvised_emag）と組み合わせると銃器三要素が揃う。
- **スコープ**:
  - 含むもの：AMMO 1種＋recipe 1件のみ
  - 含まないもの：新GUN・新MAGAZINE・新casing・新effect・item_group注入・バランス調整（Step 9）・Level3動作確認（Step 8）
- **成功基準**: Level1（`validate.sh` 通過）＋Level2（`check_mods.sh --isolated --check-errors scrap_9mm`、終了コード0＋ERRORなし）通過。Level3（Step 8）・Step 9は対象外。

### 小規模判定（Step 1・2省略根拠）
- [x] 新規ID 1個 ≤5（ITEM `scrap_9mm_handload` のみ。recipeはresult参照で新IDなし。modinfo.json除く）
- [x] 既存タイプの`copy-from`のみ（ITEM/AMMO→`9mm`、recipeは通常定義。いずれも新規`type`なし）
- [x] 既存システム拡張のみ（弾薬追加のみ。新システム・mapgen・NPC logicなし）
- [x] 同カテゴリ派生（`9mm`→粗悪手詰め弾の明確な派生。pipe_pistolとは弾薬種 `9mm` で互換＝副次効果）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | copy-from/result | 説明 |
|---|---|---|---|
| ITEM/AMMO | `scrap_9mm_handload` | copy-from `9mm` | 粗悪手詰め9mm弾 |
| recipe | （result=`scrap_9mm_handload`） | 新規レシピ（`reloaded_9mm`構成準拠：difficulty 4／gun 4／time 2 m／charges 1） | 手詰めレシピ |

衝突確認：`grep -r '"scrap_9mm_handload"' external/cdda/data/json/ mods/` が0件であること（実装前に再確認）。

### 参照ファイル（実在確認済み）
- [x] `external/cdda/data/json/items/ammo/9mm.json` — `9mm`（copy-from先）、`9mmfmj`、`reloaded_9mm`（構成参照）、`bp_9mm`（粗悪弾の目安：damage 0.76／dispersion 1.2／RECYCLED＋BLACKPOWDER）
- [x] `external/cdda/data/json/recipes/ammo/pistol.json` — `reloaded_9mm`（`LIGHT_EXERCISE`, `CC_AMMO`/`CSC_AMMO_PISTOL`, `fabrication`, difficulty 4, `["gun", 4]`, `time: 2 m`, `charges: 1`, `using: bullet_forming/ammo_bullet/ammo_9mm`, `prof_handloading`, `book_learn` 3冊）
- [x] `external/cdda/data/json/materials.json` — `brass`, `lead`, `powder` 実在
- [x] `external/cdda/data/json/ammo_effects.json` — `RECYCLED`, `BLACKPOWDER`, `COOKOFF` 実在
- [x] `external/cdda/data/json/requirements/ammo.json` — `ammo_9mm`（薬莢+雷管）実在
- [x] `external/cdda/data/json/requirements/toolsets.json` — `bullet_forming` 実在
- [x] `external/cdda/data/json/requirements/materials.json` — `ammo_bullet`（lead×1）実在
- [x] `external/cdda/data/json/proficiencies/misc.json` — `prof_handloading` 実在
- [x] `external/cdda/data/json/items/ammo.json` — `gunpowder_pistol`, `gunpowder_shotgun`, `smpistol_primer` 実在
- [x] `external/cdda/data/json/items/resources/metal.json` — `scrap`, `lead` 実在
- [x] `external/cdda/data/json/items/generic/casing.json` — `9mm_casing`、`unprimed_9mm_casing` 実在（casing継承の根拠）
- [x] `mods/small/pipe_pistol/data/items.json` — `ppis_9mm_pipe_pistol` が弾薬種 `9mm` 使用（互換根拠）

### アイテム仕様
| フィールド | 値 | 根拠 |
|---|---|---|
| id | `scrap_9mm_handload` | mod id `scrap_9mm` とは別名（混同防止） |
| copy-from | `9mm` | JHP標準弾を親とする |
| type | `ITEM` | AMMOはsubtypesで表現（親準拠） |
| name | `{"str_sp": "9x19mm JHP, scrap handload"}` | AMMO慣習。`str_pl` なし |
| description | 粗悪な手詰め9mm弾。威力・精度は劣るが材料は安い。 | 上書き |
| proportional.price | 0.7 | reloaded準拠 |
| proportional.damage | `{"damage_type": "bullet", "amount": 0.85}` | ネスト形必須。bp_9mm（0.76）の手前 |
| proportional.dispersion | 1.1 | reloaded準拠。1.2超にする場合は意図を記録 |
| extend.effects | `["RECYCLED"]` | reloaded準拠 |
| delete.flags | `["IRREPLACEABLE_CONSUMABLE"]` | reloaded準拠 |
| 継承（上書きしない） | `casing`・`ammo_type: 9mm`・重量・容量・素材 | pipe_pistol互換維持 |

注記：`delete.effects: ["NEVER_MISFIRES"]` は親に存在しないため不要（reloadedとの差異として記録のみ）。

### レシピ仕様
| フィールド | 値 | 根拠 |
|---|---|---|
| result | `scrap_9mm_handload` | 新規レシピ（result参照で新IDなし） |
| type | `recipe` | 通常定義 |
| category | `CC_AMMO` | reloaded_9mm準拠 |
| subcategory | `CSC_AMMO_PISTOL` | 同上 |
| skill_used | `fabrication` | 同上 |
| difficulty | 4 | 同上 |
| skills_required | `["gun", 4]` | flat形式でvanilla統一 |
| activity_level | `LIGHT_EXERCISE` | 0.I必須。reloaded_9mm準拠 |
| time | `2 m` | 同上 |
| charges | 1 | 同上 |
| using | `[["bullet_forming", 2], ["ammo_bullet", 2], ["ammo_9mm", 1]]` | 同上 |
| proficiencies | `[{"proficiency": "prof_handloading"}]` | 同上 |
| components | `[[["gunpowder_pistol", 3], ["gunpowder_shotgun", 3]], [["copper", 1]]]` | 同上 |
| book_learn | `[["manual_pistol", 1], ["manual_smg", 1], ["recipe_bullets", 2]]` | 既定。序盤緩和目的なら `autolearn: true` も可（いずれかを記録） |

注記：`lead` は `ammo_bullet` が既に要求するため追加しない。`scrap` 採用時は `[copper, 1]` の代替として数量つきで記録する。

### ファイル構成
- modinfo.json（type MOD_INFO, id `scrap_9mm`, dependencies `["dda"]`）
- data/ammo.json（ITEM/AMMO 1件）
- data/recipes.json（recipe 1件）

### 実装順序
1. modinfo.json
2. data/ammo.json
3. data/recipes.json

### テスト手順
1. validate.shでJSON構文チェック（Level1。各編集後に実行）
2. place_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2。完全5ステップ：mod_id確認＋debug.logのERROR有無確認）
4. CDDAを起動してLevel3確認 — **対象外（実施しない）**

### 完了条件
- [x] Level1: JSON構文OK（`validate.sh` 通過。2026-09-18確認）
- [x] Level2: 起動OK（エラーなし。`check_mods.sh --isolated --check-errors scrap_9mm` 終了コード0＋ERRORなし。2026-09-18確認、log: `logs/check_scrap_9mm_20260919_020817.log`）
- [ ] Level3: 対象外として未実施（必須・手動確認だが本計画の範囲外。Level定義の正本は `rules/verification.md`）
- [x] 新規IDが1個に収まり、小規模条件を満たす
- [ ] Step 9（バランス調整）は未実施（対象外として明記）

### Step 4整合性再確認記録
- 2026-09-18実施。すべて一致、実装続行可。
- `grep '"id": "9mm"' 9mm.json` → 1件ヒット。OK
- `reloaded_9mm`（pistol.json）→ activity_level `LIGHT_EXERCISE`、difficulty 4、skills_required `["gun", 4]`（flat形式）。OK
- `ammo_9mm`（requirements/ammo.json）、`bullet_forming`（requirements/toolsets.json）、`ammo_bullet`（requirements/materials.json）、`prof_handloading`（proficiencies/misc.json）すべて実在。OK
- name形式 `{"str_sp": "..."}`（AMMO慣習、`str_pl` なし）。OK
- recipe activity_level `LIGHT_EXERCISE` とする。OK
- `grep '"scrap_9mm_handload"'`（design.md除外）→ 0件（exit 1）。衝突なし。OK
- 親 `9mm` に `NEVER_MISFIRES` なし（`delete.effects` 不要の根拠）。flags `["IRREPLACEABLE_CONSUMABLE"]` あり（`delete.flags` の根拠）。OK
- `RECYCLED`/`BLACKPOWDER`/`COOKOFF`（ammo_effects.json）、`9mm_casing`/`unprimed_9mm_casing`（casing.json）実在。OK
- `ppis_9mm_pipe_pistol` の `ammo: ["9mm"]` 確認（互換根拠）。OK

### Step 5自己レビュー記録
- 2026-09-18実施（上記プロンプトで自己レビュー）。指摘なし、設計維持。
- ID命名：`scrap_9mm_handload` は小文字・数字・アンダースコアのみ、vanilla/既存modsと衝突なし、mod id `scrap_9mm` と別名で混同防止。OK
- copy-from：`9mm` が適切。重量・容量・素材・`ammo_type`・`casing` は継承し再宣言なし。上書きは price/damage/dispersion（proportional）＋effects extend＋flags delete のみに限定。`delete.effects` は親に該当なしのため付けない。OK
- 依存関係：`dda` のみで漏れなし（全参照IDはvanilla実在確認済み）。OK
- 修正コスト：新規ID 1＋recipe 1の最小構成。数値調整（0.85／1.1）はproportional 2行で完結し、継承破壊なし。OK
- 実データ矛盾：Step 4で全項目一致。`skills_required` flat形式、`activity_level` 必須、`book_learn` 3冊の既定を採用。OK
