## Mod設計書: wm_weapon_mastery

### 仕様書から継承
- **目的**: 武器を使い込むほど強くなる「Weapon Mastery」。モンスター撃破で装備中武器に XP が蓄積し、専用ワークベンチ（furniture）の会話 UI から XP を消費して恒常的な戦闘強化（近接ダメージ・命中・攻撃速度・遠隔ダメージ・精度）を付与する
- **スコープ**: `json_flag` / ITEM / furniture / `talk_topic` / `effect_on_condition` / `effect_type`（enchantment 参照型バフ）のみ。モンスター・マップ・レシピは含まない
- **成功基準**: 対応武器（`WM_SUPPORTED` または近接/遠隔スキル武器）を装備して撃破すると `n_wm_xp` が増加し、ワークベンチを調べて強化を選ぶと対応する `wm_buff_*` effect が付与され、キャラクターシートの戦闘数値が向上する
- **注記**: `spec.md` は未作成（本modは新規ID 28件・kill イベント駆動の新規ゲームシステムであり、CORE.md の小規模mod免除4条件を満たさない。spec 要否の最終整理は E-8 で行う）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| json_flag | `WM_SUPPORTED` | 対応武器マーカー（上限なし強化の対象） |
| ITEM | `wm_training_staff` | 修行用スタッフ（`QUARTERSTAVES`、techniques: `WBLOCK_2` / `RAPID` / `SWEEP`、`WM_SUPPORTED` 付き） |
| ITEM (TOOL) | `wm_enhance_workbench_kit` | 設置キット（`use_action: deploy_furn` → `f_wm_enhance_workbench`） |
| furniture | `f_wm_enhance_workbench` | 強化ワークベンチ（`examine_action` → `EOC_WM_OPEN_DIALOGUE`、解体でキット返却） |
| talk_topic | `TALK_WM_ENHANCE` / `TALK_WM_ENHANCE_SUCCESS` / `TALK_WM_ENHANCE_FAILURE` | 通常武器の強化 UI（5種バフ選択・成功・XP 不足） |
| talk_topic | `TALK_WM_ENHANCE_SUPPORTED` / `TALK_WM_ENHANCE_SUCCESS_SUPPORTED` / `TALK_WM_ENHANCE_FAILURE_SUPPORTED` | 対応武器の強化 UI（上限なし表示） |
| effect_on_condition | `wm_detect_category` | 装備武器の分類（`supported` / `melee` / `ranged` / `unsupported`） |
| effect_on_condition | `wm_on_kill_monster` | `character_kills_monster` イベント（`u_is_avatar` 限定）→ XP 付与 + effect 更新 |
| effect_on_condition | `wm_add_xp` | XP 加算（`min(20, max(1, _exp))`、unsupported は除外） |
| effect_on_condition | `wm_recheck` | 30秒毎の effect 再適用 |
| effect_on_condition | `wm_on_wield_item` | `character_wields_item` イベント → effect 更新 |
| effect_on_condition | `wm_update_effects` | 旧バフ除去（`u_lose_effect`）→ 装備中武器の再分類・再付与 |
| effect_on_condition | `wm_apply_buffs` | XP・バフ値を `u_*` 変数へ展開し `wm_buff_*` を付与（1 hour） |
| effect_on_condition | `EOC_WM_OPEN_DIALOGUE` / `EOC_WM_DIALOGUE_DETECT` | ワークベンチ調査 → 再分類 → 対応/通常 UI を開く |
| effect_on_condition | `EOC_WM_UPDATE_COST` / `EOC_WM_UPDATE_CAN_ENHANCE` / `EOC_WM_REFRESH_ENHANCE_STATE` | 強化コスト・可否の再計算 |
| effect_on_condition | `wm_enhance_generic` / `EOC_WM_GENERIC_ENHANCE` | 5種強化の共通実行処理 |
| effect_on_condition | `WM_TEST_VARVAL_TARGET` / `wm_test_math_comparison` | 変数・比較のテスト用 EOC |
| effect_type | `wm_buff_supported` | 対応武器バフ（`MELEE_DAMAGE` / `MELEE_TO_HIT` / `ATTACK_SPEED` / `RANGED_DAMAGE` / `WEAPON_DISPERSION` を `u_wm_*` 変数で加算・乗算） |
| effect_type | `wm_buff_common` | 通常武器バフ（同上、Tier 上限 4 は会話側で制御） |

### 参照ファイル（実在確認済み）
- [x] `rules/patterns/eoc.md` — `character_kills_monster` は全キャラ発火のため `u_is_avatar` 限定、`u_run_inv_eocs` 後の全体更新は一度だけ、`condition` の裸文字列書式
- [x] `rules/patterns/enchantment.md` — `ATTACK_SPEED` は負値で高速化、`WEAPON_DISPERSION` は `multiply` のみ、`u_lose_effect` 除去→`u_add_effect` 付与の順序、`duration` は recheck 間隔より長く
- [x] `mods/small/wm_weapon_mastery/data/effects.json` — `wm_buff_supported` / `wm_buff_common` の実在
- [x] `mods/small/wm_weapon_mastery/data/eoc.json` — `wm_*` / `EOC_WM_*` / `WM_TEST_*` 計 16 件の実在
- [x] `mods/small/wm_weapon_mastery/data/talk_topics.json` — `TALK_WM_*` 計 6 件の実在
- [ ] `external/cdda/data/json/` — copy-from 不使用（全 ID 新規定義）のため親 ID 確認は不要
- [ ] `external/cdda/data/json/recipes/` — レシピなしのため `activity_level` 確認は不要

### ファイル構成
```
mods/small/wm_weapon_mastery/
├── design.md
├── modinfo.json
└── data/
    ├── effects.json
    ├── eoc.json
    ├── furniture_and_terrain.json
    ├── items.json
    └── talk_topics.json
```

### 設計詳細

| フィールド | 値 | 根拠 |
|---|---|---|
| copy-from | なし（全定義が新規） | kill イベント駆動の XP・強化システムはバニラに前例なし |
| staff name | `{ "str_sp": "training staff" }` | 単複同形語のため `str_sp`（CORE.md name 形式） |
| kit name | `{ "str": "weapon enhancement workbench kit" }` | CORE.md: TOOL は `str` 形式 |
| furniture name | 単純文字列 `"weapon enhancement workbench"` | CORE.md: furniture 等は単純文字列必須 |
| イベント条件 | `condition: "u_is_avatar"`（裸文字列） | `rules/patterns/eoc.md`（オブジェクト形式は `unrecognized condition` エラー） |
| バフ更新 | `u_lose_effect` 全除去 → `u_run_inv_eocs` で再付与 | `rules/patterns/enchantment.md` の付け替え手順 |
| バフ duration | `1 hour`（recheck 30秒より長い） | enchantment.md の duration ルール |
| XP 加算 | `min(20, max(1, _exp))` | 1 kill の寄与を 1〜20 にクランプしインフレ防止 |
| 通常武器の強化上限 | Tier 4（会話側 `EOC_WM_UPDATE_CAN_ENHANCE` で制御） | 対応武器（`WM_SUPPORTED`）は上限なしで差別化 |

### 実装順序
1. modinfo.json（現状あり）
2. data/items.json（現状あり）
3. data/furniture_and_terrain.json（現状あり）
4. data/effects.json（現状あり）
5. data/eoc.json（現状あり）
6. data/talk_topics.json（現状あり）

### テスト手順
1. `bash scripts/validate.sh mods/small/wm_weapon_mastery/`（Level1）
2. `bash scripts/place_mod_for_test.sh --link mods/small/wm_weapon_mastery/`
3. `bash scripts/check_mods.sh --check-errors wm_weapon_mastery`（Level2）
4. CDDA 起動 → デバッグメニューで `wm_training_staff` と `wm_enhance_workbench_kit` をスポーン → キットで `f_wm_enhance_workbench` を設置 → スタッフ装備でゾンビを撃破し XP メッセージ・`u_wm_xp` 増加を確認 → ワークベンチを調べて強化を実行し、バフ effect と戦闘数値の向上を確認（Level3）

### 完了条件
- [x] Level1: JSON構文OK
- [x] Level2: 起動OK（ERROR なし）
- [ ] Level3: 意図通り動作（XP 蓄積・強化・バフ反映）— **未実行（手動確認待ち）**
