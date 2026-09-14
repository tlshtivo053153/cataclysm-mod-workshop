## Mod設計書: eoc_talk_test

### 仕様書から継承
- **目的**: EOC の変数操作・分岐 (`math` / `compare_string` / `if` / `and` / `or` / `not`) と `talk_topic` の条件・trial・effect 連携を検証するテストハーネス（`modinfo.json` の description に準拠）。デバッグ用デバイスから一括実行できる
- **スコープ**: `effect_on_condition` / `jmath_function` / `talk_topic` / デバッグ用 TOOL のみ。アイテム・レシピ・モンスター・マップ・NPC は含まない
- **成功基準**: デバッグメニュー → Run EOC → `EOC_ETT_RUN_ALL_TESTS` ですべての `[MATH]` / `[GATE]` / `[STRING]` / `[IF/ELSE]` / `[COMPOUND]` メッセージが期待値通り（`(expect ...)` 通り）に表示され、`EOC_ETT_OPEN_TALK_TEST` 経由の会話テスト（条件分岐・context_val スコープ・trial・effect）が意図通り動作する
- **注記**: `spec.md` は未作成（本modは新規ID 54件・新規ゲームシステムの検証用であり、CORE.md の小規模mod免除4条件を満たさない。spec 要否の最終整理は E-8 で行う）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）

### 使用予定ID一覧
| 種別 | ID | 説明 |
|---|---|---|
| effect_on_condition | `EOC_ETT_RUN_ALL_TESTS` | 全テストの一括実行エントリ（各 TEST 系 run_eocs + 完了メッセージ） |
| effect_on_condition | `EOC_ETT_TEST_MATH_BASIC` | 基本演算（`=`, `+=`, `*=` → 期待値 30） |
| effect_on_condition | `EOC_ETT_TEST_MATH_COMPARE` | 比較演算（`<`, `>`, `==`, `!=`, `<=`, `>=`） |
| effect_on_condition | `EOC_ETT_TEST_GATE_PATTERN` | ゲートパターン（`flag * (cond < 5)`） |
| effect_on_condition | `EOC_ETT_TEST_STRING_VAR` | 文字列変数（`u_add_var` / `compare_string` / `u_lose_var`） |
| effect_on_condition | `EOC_ETT_TEST_IF_ELSE` | if/else 分岐（数値・文字列条件） |
| effect_on_condition | `EOC_ETT_TEST_COMPOUND_COND` | 複合条件（`and` / `or` / `not`、数値+文字列混成） |
| effect_on_condition | `EOC_ETT_TEST_CTX_BASELINE` | context スコープ baseline |
| effect_on_condition | `EOC_ETT_TEST_CTX_EOC_CALLER` / `EOC_ETT_TEST_CTX_EOC_CALLEE` | EOC 呼び出し側/被呼び出し側の context 伝播 |
| effect_on_condition | `EOC_ETT_TEST_CTX_VARIABLES_CALLER` / `EOC_ETT_TEST_CTX_VARIABLES_CALLEE` | 変数スコープの呼び出し連鎖 |
| effect_on_condition | `EOC_ETT_TEST_CTX_MUTATION_CALLER` / `EOC_ETT_TEST_CTX_MUTATION_CALLEE` | mutation context 連鎖 |
| effect_on_condition | `EOC_ETT_TALK_SETUP_VARS` / `EOC_ETT_TALK_RESET` | 会話テスト用変数の setup / reset |
| effect_on_condition | `EOC_ETT_TALK_RESPONSE_EFFECT` | response effect の実行カウンタ |
| effect_on_condition | `EOC_ETT_OPEN_TALK_TEST` | 会話テストの入口（`condition: u_is_avatar`） |
| effect_on_condition | `EOC_ETT_TEST_MATH_FUNC_ONEARG` / `_MULTIARG` / `_RANDOM` / `_CONSTANTS` / `_TERNARY` / `_COMPOSE` / `_TEMPERATURE` / `_COMPOUND_ASSIGN` | math 関数群の単体テスト |
| effect_on_condition | `EOC_ETT_TEST_J_MATH_FUNC` | `jmath_function` 経由の計算テスト |
| effect_on_condition | `EOC_ETT_CTX_PRE_DIALOGUE` / `EOC_ETT_TALK_CTX_SETTER` | 会話前 context 設定 |
| jmath_function | `jmf_ett_const` / `jmf_ett_add_mul` / `jmf_ett_inner` / `jmf_ett_outer` / `jmf_ett_rand_range` | テスト用 jmath 関数（定数・四則・ネスト・乱数） |
| talk_topic | `TALK_ETT_MAIN` | テストメニュー起点（条件・context メニューへ分岐、`TALK_DONE` で終了） |
| talk_topic | `TALK_ETT_CONDITION_TEST` | 条件付き response の表示テスト |
| talk_topic | `TALK_ETT_TRIAL_RESULT` / `TALK_ETT_EFFECT_RESULT` | trial 結果 / effect 実行結果の表示 |
| talk_topic | `TALK_ETT_CTX_MENU` / `TALK_ETT_CTX_EFFECT_TOPIC` / `TALK_ETT_CTX_DISPLAY` / `TALK_ETT_CTX_FROM_EOC` / `TALK_ETT_CTX_EFFECT_DIRECT` / `TALK_ETT_CTX_DISPLAY_DIRECT` / `TALK_ETT_CTX_CHAIN_1` / `TALK_ETT_CTX_CHAIN_2` / `TALK_ETT_CTX_CHAIN_DISPLAY` / `TALK_ETT_CTX_OD_COMPARE` / `TALK_ETT_CTX_OD_VIA_TOPIC` / `TALK_ETT_CTX_OD_VIA_OD` / `TALK_ETT_CTX_OD_DISPLAY_VIA_TOPIC` / `TALK_ETT_CTX_OD_DISPLAY_VIA_OD` / `TALK_ETT_CTX_OD_DISPLAY_VIA_OD_NOTOPIC` | context_val スコープ・open_dialogue 経路の表示テスト群 |
| ITEM (TOOL) | `eoc_talk_test_item` | デバッグ用デバイス（`use_action: effect_on_conditions` → `EOC_ETT_RUN_ALL_TESTS`） |

### 参照ファイル（実在確認済み）
- [x] `rules/patterns/eoc.md` — EOC の条件書式（裸文字列条件・`u_run_inv_eocs` の per-item 注意・`math` スコープ変数）
- [x] `mods/small/eoc_talk_test/data/eoc.json` — 全 EOC ID の実在（`EOC_ETT_*` 計 29 件 + `jmf_ett_*` 計 5 件）
- [x] `mods/small/eoc_talk_test/data/talk_topics.json` — 全 talk_topic ID の実在（`TALK_ETT_*` 計 19 件）
- [ ] `external/cdda/data/json/` — copy-from 不使用（全 ID 新規定義）のため親 ID 確認は不要
- [ ] `external/cdda/data/json/recipes/` — レシピなしのため `activity_level` 確認は不要

### ファイル構成
```
mods/small/eoc_talk_test/
├── design.md
├── modinfo.json
└── data/
    ├── eoc.json
    ├── items.json
    └── talk_topics.json
```

### 設計詳細

| フィールド | 値 | 根拠 |
|---|---|---|
| copy-from | なし（全定義が新規） | テスト対象の EOC / talk_topic はバニラに前例のない組み合わせのため |
| ITEM name | `{ "str": "EOC/Talk Topic Test Device" }` | CORE.md: TOOL は `str` 形式 |
| 表示テキストの `<` `>` | 全角 `＜` `＞` に変換済み | CORE.md Step 6 チェックリスト（Bad tag エラー防止）。`<u_val:...>` 等の正当タグは半角維持 |
| `EOC_ETT_OPEN_TALK_TEST` condition | `u_is_avatar`（裸文字列） | `rules/patterns/eoc.md`: boolean 条件はオブジェクト形式不可 |

### 実装順序
1. modinfo.json（現状あり）
2. data/eoc.json（現状あり）
3. data/items.json（現状あり）
4. data/talk_topics.json（現状あり）

### テスト手順
1. `bash scripts/validate.sh mods/small/eoc_talk_test/`（Level1）
2. `bash scripts/place_mod_for_test.sh --link mods/small/eoc_talk_test/`
3. `bash scripts/check_mods.sh --check-errors eoc_talk_test`（Level2）
4. CDDA 起動 → デバッグメニュー → Run EOC → `EOC_ETT_RUN_ALL_TESTS` を実行し、各 `[MATH]` / `[GATE]` / `[STRING]` / `[IF/ELSE]` / `[COMPOUND]` メッセージが `(expect ...)` 通りか確認 → `EOC_ETT_OPEN_TALK_TEST` で会話テスト（条件分岐・context 表示・trial・effect）を順に確認（Level3）

### 完了条件
- [x] Level1: JSON構文OK
- [x] Level2: 起動OK（ERROR なし）
- [ ] Level3: 意図通り動作（全 EOC 期待値・会話テスト）— **未実行（手動確認待ち）**
