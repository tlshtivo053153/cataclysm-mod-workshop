## Mod設計書: Money World — Meridian

### 仕様書から継承

- **目的**: 死んだ経済で生き残った決済網 Meridian を別レーンの換金・購買ループとして追加する（spec.mdの背景・動機を参照）。
- **スコープ**: spec.mdの含むもの・含まないものに準拠。任意売却・NPC・クエスト・サブスクはv1.1以降。
- **成功基準**: spec.mdの成功基準に準拠（換金→購入→ランク→消失→永続→30日無限マネーなし）。

### ターゲットバージョン

- CDDA: 0.I RC

### 依存関係

- 依存mod: dda のみ

### 使用予定ID一覧

| 種別 | ID | 説明 |
|---|---|---|
| item | `mw_card` | Meridianカード（copy-from `card_plastic_abstract`） |
| item | `mw_lease_blade` | 単分子ブレード・リース品（copy-from `katana`） |
| item | `mw_lease_plate` | ハードライト・プレート・リース品（copy-from `cuirass_lightplate`） |
| spell | `mw_conjure_lease_blade` | ブレード実体化（`spawn_item`、6時間） |
| spell | `mw_conjure_lease_plate` | プレート実体化（`spawn_item`、12時間） |
| furniture | `f_mw_atm` | Meridian ATM（`examine_action` EOC） |
| overmap_terrain | `mw_branch_1` | Meridian支店（copy-from `generic_city_building`） |
| overmap_special | `mw_meridian_branch` | 支店配置（`OVERMAP_UNIQUE`） |
| mapgen | `mw_branch_1` | 支店1x1（24x24、ATMのみ） |
| item_group | `homebooks`（extend） | カード配布（`copy-from`＋`extend`） |
| recipe | `mw_card` | カード再作成 |
| EOC | `EOC_MW_REFRESH_RANK` | ランク更新 |
| EOC | `EOC_MW_OPEN_MOBILE` / `EOC_MW_OPEN_BRANCH` | 入口（携帯/支店） |
| EOC | `EOC_MW_MENU` / `EOC_MW_SHOP` / 系 | メニュー・ショップ・カテゴリ |
| EOC | `EOC_MW_SELL_SCRAP` / `EOC_MW_SELL_AMMO` / `EOC_MW_SELL_DO` | 換金2種＋共通支払い |
| EOC | `EOC_MW_SHOP_CONS` / `_TOOLS` / `_ARMOR` / `_LEASE` | カテゴリ4種 |
| EOC | `EOC_MW_BUY_<item>` ×14（inline） | 商品別購入ラッパー（selector内、ID必須） |
| EOC | `EOC_MW_BUY_BLADE_OK` / `_FAIL` / `EOC_MW_BUY_PLATE_OK` / `_FAIL` | リース成否分岐 |
| EOC | `EOC_MW_CLOSE` | メニュー終了 |
| EOC | `EOC_MW_BUY` | 通常購入（汎用＋variables） |
| EOC | `EOC_MW_BUY_BLADE` / `EOC_MW_BUY_PLATE` | リース購入2種 |
| EOC | `EOC_MW_SERVICE` / `EOC_MW_CLINIC` / `EOC_MW_SURVEY` | サービス系 |
| EOC | `EOC_MW_LEASE_CHECK` | リース期限（600秒周期） |
| u_val | `u_mw_cents` / `u_mw_total_sold` / `u_mw_rank` / `u_mw_lease_until` / `u_mw_branch` | 口座・進行変数 |

### 参照ファイル（実在確認済み）

- [x] `external/cdda/data/json/items/generic.json` — `card_plastic_abstract` 確認
- [x] `external/cdda/data/json/items/melee/swords_and_blades.json` — `katana` 確認
- [x] `external/cdda/data/json/items/armor/torso_armor.json` — `cuirass_lightplate` 確認
- [x] `external/cdda/data/json/items/resources/metal.json` — Scrap 13種＋`wire` は `generic.json` 確認
- [x] `external/cdda/data/json/items/ammo/` — `9mm`/`223`/`556`/`shot_00`/`shot_slug`/`22_lr` 確認
- [x] `external/cdda/data/json/flags.json` — `TRADER_AVOID`/`NO_SALVAGE`/`NO_REPAIR`/`NO_TAKEOFF`/`MISSION_ITEM` 確認
- [x] `external/cdda/data/json/itemgroups/books.json` — `homebooks`（distribution）確認
- [x] `external/cdda/data/json/recipes/recipe_others.json` — `activity_level` 記法確認
- [x] `external/cdda/doc/JSON/EFFECT_ON_CONDITION.md` — `u_spawn_item` flags / `u_cast_spell` true/false / `run_eoc_selector` variables / `recurrence` 秒 / `reveal_map` location変数 / `u_query` 条件 / `npc_die` アイテム削除を確認
- [x] `external/cdda/doc/JSON/NPCs.md` — `u_spawn_item` の `flags` 配列、`u_remove_item_with` の全削除を確認
- 換金ホワイトリストから `pipe` を除外（バニラ `pipe` 製作→分解で `scrap`×12の自己増殖ループになるため。Scrap 13種＋Ammo 6種の19 ID体制）
- 呪文 `flags: [NO_LEGS, NO_HANDS, SILENT]` の `SILENT` は詠唱メッセージ抑制（自販機演出）のため意図的に追加
- `u_cast_spell` の `true/false_eocs` はID文字列参照のみ（インライン記述はエンジン不安定のため不可。Level2で実証済み）
- `run_eoc_selector` 配列内のインラインEOCは `id` 必須（無名化するとバニラ連鎖エラー＋クラッシュ。Level2で実証済み）。未参照に見えても削除不可

### ファイル構成

- modinfo.json
- spec.md / design.md / README.md
- data/items/card.json / data/items/leases.json
- data/eoc/account.json / menu.json / sell.json / shop.json / service_eocs.json
- data/spells/leases.json
- data/itemgroups/meridian.json
- data/mapgen/branch.json
- data/overmap/terrain.json / special.json
- data/furniture/atm.json
- data/recipes/card.json

### 実装順序

1. modinfo.json
2. data/items/card.json、data/eoc/account.json＋menu.json（口座・メニュー骨格）
3. data/eoc/sell.json（換金2種）
4. data/eoc/shop.json＋service_eocs.json（購入・サービス）
5. data/spells/leases.json＋data/items/leases.json（リース）
6. data/itemgroups/meridian.json、data/recipes/card.json、data/furniture/atm.json
7. data/overmap/terrain.json＋special.json、data/mapgen/branch.json

### テスト手順

1. validate.shでJSON構文チェック（Level1）
2. place_mod_for_test.shでCDDAに配置
3. check_mods.shでmod読み込み確認（Level2）
4. Level3（手動。機能・悪用テスト12項目＋30日経済テストに準拠。要点のみ以下）:
   - 入手: いずれか1経路（homebooks出現/ATM再発行/レシピ作成）でカード入手→メニュー開放
   - 換金: `scrap` 100チャージ→スタック消滅・残高 `count*2` 一致・二重支払いなし。ammo代表1種（例 `9mm`）でも換金。同一品を携帯・支店で換金し料率差（50%/100%）確認。`tin`/`lead`系が選択肢に出ないこと
   - 購入: bandagesで正常・残高不足・ランク不足の3分岐（残り13品は同一EOC経由のため省略可）
   - ランク2・高額品の確認はデバッグで `u_mw_total_sold` = 50000（ランク2閾値）に設定してプレート購入で実施
   - リース: 期限後に消失（装備中・所持・地面・セーブ跨ぎ）。プレートは装着のまま期限を迎えるケースを含む。期限操作は `u_mw_lease_until` を過去時刻に設定（またはデバッグ時刻送り）
   - `u_mw_lease_until` のsave/load跨ぎ、`_FAIL`系返金分岐は到達不能な防御のため未実行として記録する
   - セーブ→ロード後に `u_mw_cents` / `u_mw_total_sold` / `u_mw_rank` が維持されること
   - 支店: デバッグreveal/テレポートでATM存在確認。死亡で残高消失、購入品14＋リース2が換金対象外であること、uncraft→換金の利益なしを確認

### 完了条件

- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作（必須・手動確認。Level定義の正本は `rules/verification.md`）
