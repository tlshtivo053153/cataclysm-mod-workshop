# EOC (Effect on Condition) 実装パターン

CDDA 0.I RC で EOC を使う際の設計パターンと落とし穴。

## 基本構造

```json
{
  "type": "effect_on_condition",
  "id": "mymod_eoc_id",
  "eoc_type": "EVENT",
  "required_event": "character_kills_monster",
  "condition": { ... },
  "effect": [ ... ]
}
```

- `type` は常に `"effect_on_condition"`
- `eoc_type`: `EVENT` / `RECURRING` / `ACTIVATION`
- `EVENT` 型では `required_event` が必須
- `RECURRING` 型では `recurrence`（秒数または時間文字列）が必須

## 条件（condition）の書き方

### boolean 条件は文字列で指定する

`u_is_avatar` 等の真偽値条件は、**オブジェクトではなく裸の文字列**で指定する。

```json
// 正しい
"condition": "u_is_avatar"

// 誤り（unrecognized condition エラー）
"condition": { "u_is_avatar": true }
```

同様の文字列形式 boolean 条件:
- `"u_is_avatar"` — プレイヤーキャラクター
- `"u_is_npc"` — NPC
- `"u_is_character"` — プレイヤーまたは NPC
- `"u_is_outside"` — 屋外
- `"u_is_alive"` — 生存中
- `"u_is_deaf"` — 聴覚なし
- `"u_is_underwater"` — 水中

### パラメータ付き条件はオブジェクトで指定する

```json
"condition": { "u_has_trait": "perk_empath" }
"condition": { "u_has_wielded_with_skill": "pistol" }
"condition": { "npc_has_flag": "WM_SUPPORTED" }
```

### 複合条件

```json
"condition": {
  "and": [
    { "u_has_trait": "perk_empath" },
    { "not": { "npc_has_flag": "FILTHY" } },
    "u_is_outside"
  ]
}
```

### 条件の可用性確認

条件名が正しくても構文を間違えると `unrecognized condition` エラーになる。boolean 条件は文字列、パラメータ付き条件はオブジェクトという区別を厳守する。

## `u_run_inv_eocs` の順序問題

`u_run_inv_eocs` はインベントリ内の各アイテムに対して `true_eocs` を実行する。
**effect の更新系処理を `u_run_inv_eocs` 内の nested EOC で per-item に呼ぶと、最後のアイテムの結果だけが残る。**

### 誤り（per-item で update を呼ぶ）
```json
// wm_add_xp（各アイテムで実行される）
{
  "effect": [
    { "math": [ "n_wm_xp = n_wm_xp + 1" ] },
    { "run_eocs": "wm_update_effects" }   // ← 各アイテムごとに全 effect が上書きされる
  ]
}
```

### 正しい（u_run_inv_eocs の後に一度だけ update を呼ぶ）
```json
// wm_on_kill_monster（イベントハンドラ）
{
  "effect": [
    {
      "u_run_inv_eocs": "all",
      "search_data": [ { "wielded_only": true } ],
      "true_eocs": [ "wm_add_xp" ]        // XP 加算のみ。更新は呼ばない
    },
    { "run_eocs": "wm_update_effects" }   // 全アイテム処理後に一度だけ更新
  ]
}
```

### 原則
- `u_run_inv_eocs` の nested EOC では**個別アイテムの状態変更のみ**を行う
- **全アイテムの状態に依存する処理**（effect の再計算など）は `u_run_inv_eocs` の**後**に一度だけ実行する

### `true_eocs` の複数ID指定

`true_eocs` は **複数の EOC ID を配列で指定可能**。配列順に逐次実行される。

```json
"true_eocs": [ "wm_detect_category", "wm_add_xp" ]
```

これにより、カテゴリ判定（detect）と後続処理（add_xp）を別 EOC に分離しつつ、同一 `u_run_inv_eocs` 内で連続実行できる。実績: `external/cdda/data/mods/TEST_DATA/EOC.json`（3ID同時指定）、`Xedra_Evolved/mutations/dhampir_eocs.json`（2〜3ID指定）。

### 同一フロー内での重複呼び出し回避

`wielded_only: true` の `u_run_inv_eocs` を同一フロー内で複数回呼ぶ場合、先行する呼び出しで実行済みの EOC を後続で重複させないこと。特に `run_eocs` で呼ばれる EOC（例: `wm_update_effects`）が内部で `u_run_inv_eocs` を実行している場合、後続の `u_run_inv_eocs` で同じ処理を再度指定すると無駄な二重実行になる。

```jsonc
// 誤り: wm_update_effects が内部で既に wm_detect_category を実行しているのに、再度指定
{
  "effect": [
    { "run_eocs": "wm_update_effects" },  // 内部で u_run_inv_eocs → wm_detect_category
    {
      "u_run_inv_eocs": "all",
      "search_data": [ { "wielded_only": true } ],
      "true_eocs": [ "wm_detect_category", "EOC_WM_DIALOGUE_DETECT" ]  // wm_detect_category 重複
    }
  ]
}

// 正しい: 先行呼び出しで実行済みの EOC は後続から除外
{
  "effect": [
    { "run_eocs": "wm_update_effects" },
    {
      "u_run_inv_eocs": "all",
      "search_data": [ { "wielded_only": true } ],
      "true_eocs": "EOC_WM_DIALOGUE_DETECT"
    }
  ]
}
```

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — `EOC_WM_OPEN_DIALOGUE` で `wm_detect_category` の二重呼び出しを解消。

## `character_kills_monster` イベント

### 利用可能なイベントコンテキスト変数

`character_kills_monster` イベントでは以下のコンテキスト変数にアクセス可能（`external/cdda/doc/JSON/EFFECT_ON_CONDITION.md:1658`）:

| 変数 | 型 | 説明 | math でのアクセス |
|------|---|---|---|
| `killer` | `character_id` | キルしたキャラクターID | 直接アクセス不可（文字列） |
| `victim_type` | `mtype_id` | モンスター種別ID | 直接アクセス不可（文字列） |
| `exp` | `int` | キル経験値（モンスター強度に比例） | `_exp` |

`int` 型のコンテキスト変数は math 式内で `_` プレフィックスでアクセス可能。`exp` は `_exp` として math で直接使用できる。

### 注意点

- `character_kills_monster` は**プレイヤー・NPC を問わず**全キャラクターで発火する
- avatar のみに限定するには `"condition": "u_is_avatar"` を使用する
- **`_exp` は `u_run_inv_eocs` 内の nested EOC でも引き続きアクセス可能**（後述「`_` 変数と `u_run_inv_eocs`」参照）

## `math` の変数スコープ

| スコープ | プレフィックス | 例 | 備考 |
|----------|---------------|-----|------|
| キャラクター変数 | `u_` | `u_val('power')` | プレイヤー/NPC の変数 |
| NPC/アイテム変数 | `n_` | `n_wm_xp` | `u_run_inv_eocs` 内ではアイテム変数 |
| グローバル変数 | `global_` | `global_xp` | セーブデータ全体で共有 |
| コンテキスト変数 | `_` | `_exp` | イベントから渡される値 |

- `n_` スコープの変数は `u_run_inv_eocs` の nested EOC 内でのみアイテムに保存される
- アイテム変数の永続性（セーブロード後も維持されるか）は**実機確認が必要**
- 変数が未定義の場合、math では `0` として扱われる
- **`u_` 変数は明示的な再代入がない限り前回の値が残留する。** 複数分岐を含む EOC で `u_` 変数を使う場合、全分岐で変数を明示的に設定しなければ、過去の EOC 実行で設定された値が次の実行で誤って参照される可能性がある。分岐が変数を使わない場合でも、防御的初期化として 0 代入を行うこと。ただし、EOC 内で閉じた一時変数（`_` プレフィックス）を使う場合は残留リスクがないため、分岐の前に防御的初期化を置くだけでよい。実績: `EOC_WM_UPDATE_CAN_ENHANCE` の先頭で `_melee = 0` / `_ranged = 0` を防御的初期化し、分岐内で 1 を代入
- **`n_` 変数は enchantment の math 式から直接アクセス不可。** enchantment の math はキャラクターコンテキスト（`u_`）で評価されるため、アイテム変数を参照したい場合は EOC で `n_` → `u_` にコピーしてから effect を付与する（`rules/patterns/enchantment.md` の「変数スコープの制約」参照）
- **`u_` 変数は `u_run_inv_eocs` 内から読み取り可能。** talk_topic や親EOCで設定した `u_` math 変数は、`u_run_inv_eocs` の nested EOC（アイテムスコープ）内でも `u_` プレフィックスでアクセス可能。CDDA 公式ドキュメント（`EFFECT_ON_CONDITION.md`）で `u_run_inv_eocs` はデュアルトーカーモデルを維持し、alpha talker（`u_`）はキャラクターのまま、beta talker（`n_`）にアイテムが割り当てられると明記されている。両スコープが同時にアクセス可能であり、math 変数の `u_` プレフィックスは常に alpha talker にスコープされる（`NPCs.md`）。実績: `wm_apply_buffs` が既に `u_run_inv_eocs` 内で `u_` math 変数への書き込みを行っている。
- **`_` プレフィックスのイベントコンテキスト変数（`_exp` 等）も `u_run_inv_eocs` 内からアクセス可能。** beta talker が monster から inventory item に置き換わっても、`_` スコープの変数は消滅しない。`u_run_inv_eocs` の nested EOC 内で `_exp` を直接参照できる。`wm_weapon_mastery` の `wm_on_kill_monster` → `wm_add_xp` フローで実績確認済み。

## message 内の変数埋め込み

```json
{ "u_message": "<npc_val:wm_xp>", "type": "info" }
```

- `<global_val:変数名>` — グローバル変数
- `<context_val:変数名>` — イベントコンテキスト変数
- `<npc_val:変数名>` — NPC/アイテム変数（`u_run_inv_eocs` 内でのみ意味を持つ）
- `<u_val:変数名>` — プレイヤー変数。`u_message` および `talk_topic` の `dynamic_line` で使用可能。math 変数（`u_xxx`）の値（数値）を表示できる。実績: BombasticPerks（`<u_val:current_level>`）、MindOverMatter（`<u_val:teleport_total_carried_volume>`）、Xedra Evolved（`<u_val:blood_amount_for_graph>`）
- **未定義変数のタグが正しく置換されるかは実機確認が必要**（空文字列になる可能性がある）

### `<npc_val>` の評価タイミングと逐次実行

`then` 配列（または `effect` 配列）内のアクションは**上から下へ逐次実行**される。このため、math 代入の**後**に `u_message` を配置すれば、message 内の `<npc_val:変数>` タグは代入後の新しい値を表示する。

```jsonc
// 正しい: 代入→表示の順で逐次実行されるため、<npc_val:wm_buff_melee_damage> は新しいTier(1〜4)を表示
"then": [
  { "math": [ "n_wm_buff_melee_damage = n_wm_buff_melee_damage + 1" ] },
  { "u_message": "近接ダメージ強化 Tier <npc_val:wm_buff_melee_damage> を取得しました！", "type": "good" }
]

// もし順序を逆にすると、古い値が表示される
```

この逐次実行の保証は CDDA の EOC エンジン（`effect_on_condition.cpp`）の実装に基づく。同一配列内の要素は `for (auto &eff : effects)` のループで順次処理される。

## `open_dialogue` の構文

EOC の effect から対話（talk_topic）を開くには `open_dialogue` を使用する。値は **`topic` キーを持つオブジェクト**で指定する。

```json
// 正しい
{ "open_dialogue": { "topic": "TALK_MY_DIALOGUE" } }

// 誤り（Unread data エラー。裸の文字列は不可）
{ "open_dialogue": "TALK_MY_DIALOGUE" }
```

### `open_dialogue` と変数定義の順序

talk_topic の response `condition`（`{ "math": [ "u_var == 1" ] }`）は `open_dialogue` が実行された**その時点**の変数値で評価される。変数定義より**前に** `open_dialogue` があると、未定義変数（math 変数はデフォルト 0）で condition が評価され、期待と異なる表示になる。

```jsonc
// 誤り: open_dialogue が先、can_enh 変数は後 → talk_topic condition 評価時は 0
{
  "effect": [
    { "open_dialogue": { "topic": "TALK_WM_ENHANCE" } },
    { "math": [ "u_wm_can_enh_melee_damage = (n_wm_buff_melee_damage < 4)" ] }
  ]
}

// 正しい: 全変数を定義した後で open_dialogue
{
  "effect": [
    { "math": [ "u_wm_can_enh_melee_damage = (n_wm_buff_melee_damage < 4)" ] },
    { "open_dialogue": { "topic": "TALK_WM_ENHANCE" } }
  ]
}
```

**注意**: `open_dialogue` は EOC 実行を**中断しない**。`open_dialogue` の後にも effect 配列の残りは逐次実行されるが、ダイアログ表示は既に開始しているため、後続の変数代入は talk_topic の condition 評価に**反映されない**。すべての変数計算を `open_dialogue` より前に配置すること。

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — `EOC_WM_DIALOGUE_DETECT` で `EOC_WM_REFRESH_ENHANCE_STATE` を `run_eocs` で実行後に `open_dialogue` を配置。

### talk_topic response effect 内の `open_dialogue` と context_val の制約

talk_topic の response `effect` 配列内で `open_dialogue` を使う場合、EOC 内とは異なる以下の制約がある。

#### context_val は引き継がれない

EOC 内の `open_dialogue` や通常の `topic` 遷移では `context_val` が引き継がれるが、**talk_topic response effect 内の `open_dialogue` 経由では `context_val` は引き継がれない**（空文字列になる）。

```jsonc
// VIA_OD: effect 内で context_val を設定し open_dialogue
{
  "text": "実行",
  "effect": [
    { "set_string_var": "value", "target_var": { "context_val": "my_var" } },
    { "open_dialogue": { "topic": "TALK_DISPLAY" } }
  ],
  "topic": "TALK_ORIGINAL"  // 元の会話を維持
}

// TALK_DISPLAY: context_val は空文字
// "dynamic_line": "context_val: '<context_val:my_var>'"  → ""
```

**回避策**: `context_val` と同時に `u_val` fallback をセットし、遷移先で `<u_val:変数名>` で値を確認する。

```jsonc
"effect": [
  { "set_string_var": "value", "target_var": { "context_val": "my_var" } },
  { "set_string_var": "value_bk", "target_var": { "u_val": "my_var_bk" } },
  { "open_dialogue": { "topic": "TALK_DISPLAY" } }
]

// TALK_DISPLAY: u_val fallback で値が確認できる
// "dynamic_line": "context_val: '<context_val:my_var>'\nu_val fallback: '<u_val:my_var_bk>'"
```

#### effect の表示タイミング

talk_topic response effect 配列内に `open_dialogue` がある場合、`u_message` 等の表示系 effect は **`open_dialogue` 先の会話が終了した後に**表示される。effect 配列の先頭で設定した `u_message` でも即時表示はされない。

```jsonc
// この u_message は DISPLAY_VIA_OD 会話が TALK_DONE で閉じた後に表示される
"effect": [
  { "set_string_var": "val", "target_var": { "context_val": "var" } },
  { "u_message": "[TEST] context_val を設定しました", "type": "info" },
  { "open_dialogue": { "topic": "TALK_DISPLAY" } }
]
```

#### topic 省略時の注意

talk_topic response で `topic` フィールドを省略した場合、**effect 配列は一切実行されず**、親トピックに戻るのみ。`open_dialogue` も `set_string_var` も `u_message` も発火しない。

```jsonc
// 誤り: topic 省略 → effect 未実行。open_dialogue も発火しない
{
  "text": "実行",
  "effect": [
    { "set_string_var": "value", "target_var": { "context_val": "my_var" } },
    { "open_dialogue": { "topic": "TALK_SOME_DIALOGUE" } }
  ]
  // topic なし → 遷移先がないため effect はスキップされる
}
```

response に `open_dialogue` を使う場合は**必ず `"topic"` を明示**し、元の会話スタックを維持すること。

**実績**: `mods/small/eoc_talk_test/data/talk_topics.json` — `TALK_ETT_CTX_OD_VIA_OD` で 3 パターン（topic 遷移 / open_dialogue + topic 明示 / topic 省略）の context_val 引き継ぎテストを実装。

### 表示テキスト内の `<` `>` 文字の全角化

CDDA のタグパーサ（`src/npctalk.cpp:2607` `parse_tags`）は `<タグ名:...>` 形式のタグを解釈する。このため、表示テキスト（`u_message`, talk_topic の `text` / `dynamic_line`）内に比較演算子として `<` `>` を含めると、タグの開始・終了と誤認されて `Bad tag` エラーやテキスト途切れが発生する。

**影響範囲**:
- `u_message` の表示文字列
- talk_topic の `text`（response 選択肢テキスト）
- talk_topic の `dynamic_line`
- その他、画面に表示されるすべての文字列

**影響を受けないもの**:
- math 式文字列（`"u_test_a < 5"`）→ タグパーサを通らない
- condition 内の式（`{ "math": [ "u_val >= 10" ] }`）→ タグパーサを通らない
- 正当なタグ（`<u_val:xxx>`, `<context_val:xxx>`, `<npc_val:xxx>` 等）→ 半角のまま維持

**解決策**: 表示テキスト内の比較演算子 `<` `>` を全角 `＜`（U+FF1C）`＞`（U+FF1E）に置換する。`<=` は `＜=`、`>=` は `＞=` と書く。

```jsonc
// 誤: 半角 < > が u_message 内にある
{ "u_message": "[MATH COMPARE] lt (5<10): <u_val:test_lt> (expect 1)" }

// 正: 比較演算子のみ全角化。タグ <u_val:...> は半角のまま
{ "u_message": "[MATH COMPARE] lt (5＜10): <u_val:test_lt> (expect 1)" }
```

```jsonc
// talk_topic response text でも同様
// 誤
{ "text": "math >= 40（条件を満たす場合のみ表示）" }

// 正
{ "text": "math ＞= 40（条件を満たす場合のみ表示）" }
```

**実績**:
- `mods/small/wm_weapon_mastery/data/eoc.json` — `u_message` 内で `＜` を使用（`2＜4 expect 1`）
- `mods/small/eoc_talk_test/data/eoc.json` — 全 `u_message` で比較演算子を全角化
- `mods/small/eoc_talk_test/data/talk_topics.json` — response `text` 内の `>=` を `＞=` に全角化

### カテゴリフラグによるゲーティングパターン

近接/遠隔などカテゴリによって表示を切り替える場合、カテゴリフラグ（`_melee` / `_ranged` 等の一時変数）を乗数に使うことで分岐内のゼロ初期化を省略できる。

```jsonc
// EOC の先頭で一時変数を防御的初期化、分岐で 0/1 に設定した後に共通ブロックを配置
{ "math": [ "_melee = 0" ] },
{ "math": [ "_ranged = 0" ] },
// 分岐（_melee を 0/1 に設定）
{ "if": { "compare_string": [ "melee", { "npc_val": "wm_wcat" } ] },
  "then": [ { "math": [ "_melee = 1" ] } ] },
// 共通ブロック
{ "math": [ "u_wm_can_enh_melee_damage = _melee * (n_wm_buff_melee_damage < 4)" ] },
// melee → _melee=1 → can_enh = 0 or 1 (buffに応じて)
// ranged → _melee=0 → can_enh = 0 (常に非表示)
// supported → _melee=1 → can_enh = 0 or 1

{ "math": [ "u_wm_can_enh_ranged_damage = _ranged * (n_wm_buff_ranged_damage < 4)" ] },
// ranged → _ranged=1, melee → 0 → can_enh は ranged 時のみ有効値
```

**前提**:
- ゲートに使うフラグ変数（`_melee` / `_ranged`）がこの式より**前に**分岐内で定義されていること
- EOC の先頭で防御的初期化（`_melee = 0`）を行っていること
- 比較演算子 `<` `>` `>=` `<=` が math 代入文の右辺値として 0/1 を返すこと。CDDA 0.I RC で**実績あり**（`wm_test_math_comparison` EOC で確認済み）。

**利点**:
- 分岐（melee/ranged/supported）内のゼロ初期化が不要になる
- 全カテゴリ共通の計算を一箇所に集約できる
- talk_topic の response `condition` に直接使える非ゼロの値が得られる

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — `EOC_WM_UPDATE_CAN_ENHANCE` で 5 種の can_enh 変数を共通ブロック化。カテゴリ分岐から共通計算を分離。

### EOC から talk_topic へ遷移した後の戻り先制御（旧パターン・非推奨）

かつては `open_dialogue` で対話を開いた後、結果ページから元の対話に戻る際に **`u_` 変数に戻り先を記録**するパターンが使われていた。このパターンでは複数の talk_topic を用意し、`u_wm_last_dialogue` で戻り先を分岐する必要があった。

```json
// 非推奨: 対話を開く前に u_ 変数で戻り先をマーク
{ "math": [ "u_wm_last_dialogue = 1" ] },
{ "open_dialogue": { "topic": "TALK_WM_ENHANCE_MELEE" } }

// 非推奨: TALK_RESULT の「続ける」選択肢で戻り先を分岐
{
  "type": "effect_on_condition",
  "id": "EOC_RETURN_TO_DIALOGUE",
  "effect": [
    {
      "if": { "math": [ "u_wm_last_dialogue == 1" ] },
      "then": [ { "open_dialogue": { "topic": "TALK_WM_ENHANCE_MELEE" } } ]
    },
    {
      "if": { "math": [ "u_wm_last_dialogue == 2" ] },
      "then": [ { "open_dialogue": { "topic": "TALK_WM_ENHANCE_RANGED" } } ]
    }
  ]
}
```

### 推奨パターン: talk_topic response の `condition` で動的フィルタリング + 単一トピック + trial 判定

talk_topic を**単一の共通トピック**に統合し、各 response に `condition` フィールドで表示可否を制御する。さらに `trial` フィールドで必要 XP の有無をチェックし、成功/失敗で別トピックに分岐する。戻り先は直接 `topic` を指定するため、専用の戻り用 EOC は不要。

```jsonc
// EOC 側: EOC_WM_REFRESH_ENHANCE_STATE で cost + can_enh を計算し、
// EOC_WM_DIALOGUE_DETECT が run_eocs でリフレッシュ後に open_dialogue
{
  "id": "EOC_WM_DIALOGUE_DETECT",
  "effect": [
    { "run_eocs": "EOC_WM_REFRESH_ENHANCE_STATE" },
    { "open_dialogue": { "topic": "TALK_WM_ENHANCE" } }
  ]
}

// talk_topic 側: response に condition + trial でフィルタリング
{
  "type": "talk_topic",
  "id": "TALK_WM_ENHANCE",
  "responses": [
    {
      "text": "近接ダメージ強化 [<u_val:wm_cost_melee_damage> XP]",
      "condition": { "math": [ "u_wm_can_enh_melee_damage" ] },
      "trial": { "type": "CONDITION", "condition": { "math": [ "u_wm_cost_melee_damage <= u_wm_xp" ] } },
      "success": {
        "topic": "TALK_WM_ENHANCE_SUCCESS",
        "effect": [ { "math": [ "u_wm_enhance_type = 1" ] }, { "run_eocs": [ "EOC_WM_GENERIC_ENHANCE" ] } ]
      },
      "failure": { "topic": "TALK_WM_ENHANCE_FAILURE" }
    }
  ]
}

// 成功時の戻り: 直接 topic で戻る（EOC_WM_RETURN_TO_DIALOGUE 不要）
{
  "type": "talk_topic",
  "id": "TALK_WM_ENHANCE_SUCCESS",
  "dynamic_line": "強化の結果が表示されました。",
  "responses": [
    {
      "text": "戻る",
      "topic": "TALK_WM_ENHANCE",
      "effect": {
        "u_run_inv_eocs": "all",
        "search_data": [ { "wielded_only": true } ],
        "true_eocs": "EOC_WM_REFRESH_ENHANCE_STATE"
      }
    }
  ]
}
```

**注意点**:
- `condition` 内の `{ "math": [ "u_var" ] }` は変数が非ゼロのとき true として評価される。`== 1` との明示比較は不要（math 変数はデフォルト 0）。なお、文字列変数との比較には `{ "compare_string": [ "expected", { "u_val": "var" } ] }` も使用可能。
- 未定義の math 変数は `0` として評価される。このため `u_var` 単独での判定は未定義時も false（0）になる。
- 戻り先の再検出は不要。プレイヤーは対話中で武器が変わらないため、初回に設定された `u_wm_can_enh_*` がそのまま有効。戻る際は `u_run_inv_eocs` で `EOC_WM_REFRESH_ENHANCE_STATE` を再実行して状態を最新化する。
- `trial` フィールドを使うことで、talk_topic 内で XP 不足を判定して別トピックに分岐できる。talk_topic から EOC を介さずに成功/失敗の分岐が可能になる。

**利点**:
- 複数トピックの重複コードを単一トピックに統合できる
- EOC 側の戻り先管理（`u_wm_last_dialogue`）が不要になり、コードが簡潔になる
- 武器カテゴリに応じた選択肢の表示/非表示をトピックレベルで宣言的に記述できる

**実績**: `mods/small/wm_weapon_mastery/data/talk_topics.json` — 1トピックで condition + trial による動的フィルタリングとXPチェック。戻りは直接 `topic` によるリダイレクト。

### talk_topic 応答からの EOC 呼び出し

talk_topic の response から EOC を実行するには `"effect"` フィールドに `"run_eocs"` を指定する。

```json
{
  "type": "talk_topic",
  "id": "TALK_WM_ENHANCE",
  "dynamic_line": "強化項目を選んでください。",
  "responses": [
    {
      "text": "近接ダメージ強化",
      "topic": "TALK_WM_ENHANCE_SUCCESS",
      "effect": { "run_eocs": [ "EOC_WM_ENHANCE_MELEE_DAMAGE" ] }
    }
  ]
}
```

**制約:**
- `talk_topic` の `dynamic_line` からは **item/npc 変数 (`n_`) を直接参照できない**。アイテム変数の値は `<npc_val:>` では表示不可（talk_topic に NPC がいない場合）。アイテム変数を表示するには、事前に `math` で `u_` 変数にコピーし、`<u_val:>` で表示する（後述の「`n_` → `u_` コピー + `<u_val:>` 表示パターン」参照）。
- `talk_topic` の response `topic` フィールドには **変数による条件分岐が使えない**。動的な戻り先選択が必要な場合は上記の `u_` 変数 + 専用 EOC パターンを使う。

### talk_topic response effect の配列構文

talk_topic の response `effect` は **配列形式**にも対応しており、`math` 代入と `run_eocs` を同一レスポンス内で順次実行できる。CDDA は配列要素を上から下へ逐次処理するため、代入→EOC呼び出しの順序が保証される。

```json
// 単一の run_eocs（従来）
"effect": { "run_eocs": [ "EOC_WM_ENHANCE_MELEE_DAMAGE" ] }

// 配列形式: math でルーティング変数を設定 → run_eocs で汎用EOCを呼ぶ
"effect": [
  { "math": [ "u_wm_enhance_type = 1" ] },
  { "run_eocs": [ "EOC_WM_GENERIC_ENHANCE" ] }
]
```

**実績**:
- `data/json/npcs/missiondef.json:927` — バニラで `effect` 配列に `math` + `run_eocs` 混在
- `data/json/npcs/isherwood_farm/NPC_Chris_Isherwood.json:768` — 同様の使用例
- `mods/small/wm_weapon_mastery/data/talk_topics.json` — 5つの response を配列形式で統一

### talk_topic response の `trial` によるリソースチェック

talk_topic の response に `trial` フィールドを指定することで、EOC を介さずに talk_topic 内で条件チェックと分岐が可能になる。`trial` の condition が true なら `success`、false なら `failure` に分岐し、それぞれで別の `topic` と `effect` を指定できる。

```jsonc
{
  "text": "近接ダメージ強化 [<u_val:wm_cost_melee_damage> XP]",
  "condition": { "math": [ "u_wm_can_enh_melee_damage" ] },
  "trial": { "type": "CONDITION", "condition": { "math": [ "u_wm_cost_melee_damage <= u_wm_xp" ] } },
  "success": {
    "topic": "TALK_WM_ENHANCE_SUCCESS",
    "effect": [
      { "math": [ "u_wm_enhance_type = 1" ] },
      { "run_eocs": [ "EOC_WM_GENERIC_ENHANCE" ] }
    ]
  },
  "failure": {
    "topic": "TALK_WM_ENHANCE_FAILURE"
  }
}
```

**構成要素**:
- `condition` — 選択肢の表示可否（`can_enh_*` 変数で制御）
- `trial` — `{ "type": "CONDITION", "condition": { ... } }` 形式。選択肢が選ばれた後にチェックされる
- `success` — trial 成功時の `topic` と `effect`
- `failure` — trial 失敗時の `topic`（effect は通常不要）

**利点**:
- リソースチェック（XP 不足等）を EOC 側ではなく talk_topic 側で宣言的に記述できる
- 成功/失敗で別トピックに分岐するため、結果表示がシンプルになる
- チェック用の専用 EOC が不要

**注意**: `trial` の condition が false の場合、response の `effect` は実行されず `failure.topic` に直接遷移する。このため、`effect` での代入や副作用は `success.effect` に記述する必要がある。

**実績**: `mods/small/wm_weapon_mastery/data/talk_topics.json` — 5つの強化選択肢すべてで `trial` を使用し、XP不足時のエラーページ分岐を実装。

### talk_topic response `effect` 内での `u_run_inv_eocs` による状態更新

talk_topic の response `effect` 配列内で `u_run_inv_eocs` を使用し、戻り先トピックに遷移する前に per-item の状態を再計算できる。`topic` による直接リダイレクトと組み合わせることで、専用の戻り用 EOC（`open_dialogue` を持つ EOC）が不要になる。

```jsonc
// 強化結果ページ → 強化選択ページに戻る際、cost / can_enh を最新化
{
  "type": "talk_topic",
  "id": "TALK_WM_ENHANCE_SUCCESS",
  "dynamic_line": "強化の結果が表示されました。",
  "responses": [
    {
      "text": "戻る",
      "topic": "TALK_WM_ENHANCE",
      "effect": [
        {
          "u_run_inv_eocs": "all",
          "search_data": [ { "wielded_only": true } ],
          "true_eocs": "EOC_WM_REFRESH_ENHANCE_STATE"
        }
      ]
    }
  ]
}
```

**利点**:
- 戻り先用の専用 EOC（旧 `EOC_WM_RETURN_TO_DIALOGUE`）が不要
- `topic` による遷移と `effect` による状態更新を 1 つの response に集約できる
- コードの流れが読みやすい（「戻る → 更新 → 次のトピック」の順序が明示的）

**注意**: `effect` 配列内の `u_run_inv_eocs` は、`topic` によるトピック遷移の前に実行される。CDDA の response 処理は effect → topic の順序で行われるため、更新後の状態で戻り先トピックが表示される。

**実績**: `mods/small/wm_weapon_mastery/data/talk_topics.json` — `TALK_WM_ENHANCE_SUCCESS` の「戻る」で `EOC_WM_REFRESH_ENHANCE_STATE` を実行。

### `dynamic_line` での `u_` 変数表示: `n_` → `u_` コピー + `<u_val:>` パターン

talk_topic の `dynamic_line` では `<u_val:変数名>` でプレイヤー変数の値を直接表示できる。アイテム変数（`n_`）を `dynamic_line` に表示したい場合は、対話を開く**前に**アイテム変数をプレイヤー変数にコピーする。

```jsonc
// EOC_WM_OPEN_DIALOGUE: 対話を開く前に wm_update_effects を実行
// wm_update_effects が wm_detect_category + wm_apply_buffs を呼び n_ → u_ コピーを行う
// そのため 2つ目の u_run_inv_eocs では wm_detect_category は不要（実行済み）
{
  "type": "effect_on_condition",
  "id": "EOC_WM_OPEN_DIALOGUE",
  "effect": [
    { "run_eocs": "wm_update_effects" },  // ★ 事前に u_ 変数を同期
    {
      "u_run_inv_eocs": "all",
      "search_data": [ { "wielded_only": true } ],
      "true_eocs": "EOC_WM_DIALOGUE_DETECT"
    }
  ]
}

// wm_apply_buffs: item の n_wm_buff_* → player の u_wm_* にコピー
// n_wm_xp → u_wm_xp もコピー（dynamic_line 表示用）
"effect": [
  { "math": [ "u_wm_xp = n_wm_xp" ] },  // ★ XP も u_ にコピー
  { "math": [ "u_wm_melee_damage = n_wm_buff_melee_damage" ] },
  // ...
]
```

コピー後、`dynamic_line` で `<u_val:>` を使って表示:

```jsonc
// talk_topics.json
{
  "type": "talk_topic",
  "id": "TALK_WM_ENHANCE",
  "dynamic_line": "近接ダメージ: Tier <u_val:wm_melee_damage>/4\n保有XP: <u_val:wm_xp>"
}
```

**注意点:**
- `<u_val:>` は math 変数（`u_xxx`）の**数値**をそのまま表示する。文字列変数（`u_add_var` で設定）も表示可能
- 未定義の変数は `0` として表示される
- `u_run_inv_eocs` で複数アイテムを処理すると最後のアイテムの値だけが残るため、`wielded_only: true` で wield 中の武器だけに限定する
- `dynamic_line` 内の `"math"` 条件（`{ "math": [...], "yes": "...", "no": "..." }`）では `&&` / `||` が使えず、`"and"` / `"or"` も利用不可。値の範囲チェックが必要な場合は `<u_val:>` で直接数値表示する方が簡潔

**実績**: `mods/small/wm_weapon_mastery/data/talk_topics.json` — 1つの talk_topic で `<u_val:>` を使用したバフ状態表示

## EOC の最小構成と推奨構成

最小の RECURRING EOC:
```json
{
  "type": "effect_on_condition",
  "id": "mymod_recheck",
  "recurrence": "30 seconds",
  "effect": { "run_eocs": "mymod_update" }
}
```

最小の EVENT EOC:
```json
{
  "type": "effect_on_condition",
  "id": "mymod_on_kill",
  "eoc_type": "EVENT",
  "required_event": "character_kills_monster",
  "effect": [ { "u_message": "kill event", "type": "info" } ]
}
```

## `math` 式の演算子制約

CDDA の `math` 式は C 言語風だが、以下の演算子は **未サポート**:

| 未サポート | 代替手段 |
|---|---|
| `\|\|` (論理OR) | JSON レベルの `"or"` 条件で囲む（後述） |
| `&&` (論理AND) | JSON レベルの `"and"` 条件で囲む |
| `!` (論理NOT) | `"not"` 条件で囲むか、`!=` / `==` の反転 |

### `||` の代替: JSON `"or"` 条件

```json
// 誤り（"Unknown operator |" エラー）
{ "math": [ "n_wm_wcat == 1 || n_wm_wcat == 3" ] }

// 正しい
{
  "or": [
    { "math": [ "n_wm_wcat == 1" ] },
    { "math": [ "n_wm_wcat == 3" ] }
  ]
}
```

### `&&` の代替: JSON `"and"` 条件

```json
// 誤り
{ "math": [ "n_val > 0 && n_val < 10" ] }

// 正しい
{
  "and": [
    { "math": [ "n_val > 0" ] },
    { "math": [ "n_val < 10" ] }
  ]
}
```

**理由**: `math` 式は算術演算のみをサポートし、論理演算子は EOC 条件レベルで JSON 構造として扱われる。CDDA 0.I RC 時点。

### 複合算術式（括弧付き演算）の使用

`math` 条件式では、**括弧を使った複合算術式がサポートされている**。変数を含む演算式の一部として動的コスト計算が可能。

```jsonc
// 条件: n_wm_xp >= (n_wm_buff_melee_damage + 2) — 動的XPコスト
{ "if": { "math": [ "n_wm_xp >= (n_wm_buff_melee_damage + 2)" ] } }

// 代入: XPから動的コストを減算
{ "math": [ "n_wm_xp = n_wm_xp - (n_wm_buff_melee_damage + 2)" ] }
```

**実績**:
- `MindOverMatter/nether_attunement.json` L18: `u_vitamin(...) >= (2 + u_skill(...) * 2)`
- `hallucination_eocs.json` L110: `(u_hp('ALL') * 1.4) < u_hp_max('bp_null')`
- `mods/small/wm_weapon_mastery/data/eoc.json` — 動的ティアコスト計算（後述）

### 利用可能な算術関数

CDDA の math 式では以下の算術関数が使用可能:

| 関数 | 構文 | 説明 | 実績 |
|------|------|------|------|
| `min` | `min(a, b)` | 2引数の小さい方を返す | MindOverMatter, Xedra Evolved, Magiclysm, wm_weapon_mastery: `min(20, max(1, _exp))` |
| `max` | `max(a, b)` | 2引数の大きい方を返す | 同上 |
| `clamp` | `clamp(x, lo, hi)` | x を [lo, hi] の範囲に制限。**`hi > lo` が必須**（逆転は未定義動作・クラッシュリスク。`rules/common_errors.md` 参照） | バニラ EOC で広く使用 |

`min` / `max` の典型的なユースケース:

```jsonc
// 下限 1、上限 20 の XP スケーリング
{ "math": [ "n_wm_xp = n_wm_xp + min(20, max(1, _exp))" ] }

// 上限制限のみ (0 以上を保証する場合は max 不要)
{ "math": [ "u_val = min(100, u_val)" ] }
```

`clamp` の代替として `min` + `max` の組み合わせも使えるが、3値制限には `clamp` の方が簡潔。`min` / `max` が適しているのは**式の一部として上限/下限のいずれか一方のみ**を適用したい場合。

**参照**: `external/cdda/doc/JSON/NPCs.md:1307`

### 動的ティアアップグレードパターン

ティア段階（レベル1〜4）のアップグレードを実装する際、各ティアを個別の条件分岐でハードコードする代わりに、現在のティア値を用いた**動的コスト計算**で全ティアを単一の条件ブロックに統合できる。

**ハードコードパターン（非推奨, ~90行）**:
```jsonc
// 各ティアごとに分岐を書く（4ティア分で約56行）
{ "if": { "math": [ "n_buff == 0" ] }, "then": [
  { "if": { "math": [ "n_xp >= 2" ] }, "then": [
    { "math": [ "n_xp = n_xp - 2" ] },
    { "math": [ "n_buff = 1" ] }
  ], "else": [ { "u_message": "XP不足。必要: 2" } ] }
] },
{ "if": { "math": [ "n_buff == 1" ] }, "then": [
  { "if": { "math": [ "n_xp >= 3" ] }, "then": [ ... ] }
] },
// ... tier 2, 3 も同様
```

**動的パターン（推奨, ~27行）**:
```jsonc
{
  "if": { "math": [ "n_buff >= 4" ] },
  "then": [
    { "u_message": "既に最大レベルです。", "type": "bad" }
  ],
  "else": [
    {
      "if": { "math": [ "n_xp >= (n_buff + 2)" ] },
      "then": [
        { "math": [ "n_xp = n_xp - (n_buff + 2)" ] },
        { "math": [ "n_buff = n_buff + 1" ] },
        { "u_message": "強化 Tier <npc_val:buff> を取得しました！", "type": "good" }
      ],
      "else": [
        { "u_message": "XPが不足しています。 (現在XP: <npc_val:xp>)", "type": "bad" }
      ]
    }
  ]
}
```

**コストの設計**:
- `buff_var + N` で動的コストを計算。`N` は定数（例: Tier 0→1 の場合は `N=2`、XPコストは 2→3→4→5 と進行）
- コストが線形増加する場合に特に有効。非線形の場合は別途検討
- `<npc_val:buff_var>` の評価タイミングは上記「逐次実行」セクションを参照

**複数EOCでのテンプレート化**:
CDDA の EOC はパラメータを受け取れないため、同じ構造で変数名とメッセージだけが異なる EOC を複数定義する場合は、1つ目のEOCをテンプレートとして実装→検証→残りを複製する手順が安全。

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — 5つの nested EOC を動的パターンで統一（728行→463行, -36%）

### 結果コードによる計算/表示の分離

動的ティアアップグレードパターンと switch/case を組み合わせる際、**結果コード**（`u_wm_upgrade_result`）を使って計算フェーズと表示フェーズを分離する。

**問題**: switch/case の各 case 内で if/else をネストさせると、メッセージ表示と計算ロジックが混在し、case 追加時のコピペ量が増える。

**解法**: 計算結果を 3 値の結果コードに集約し、switch/case は結果コードだけを見る:

```jsonc
// 計算フェーズ: 結果コードに集約（デフォルト→上書きの順序で排他ルーティング）
{ "math": [ "u_wm_upgrade_result = 3" ] },        // デフォルト: XP不足
{
  "if": { "math": [ "n_wm_upgrade_tier >= 4" ] },
  "then": [ { "math": [ "u_wm_upgrade_result = 2" ] } ]  // 上書き: 最大レベル
},
{
  "if": { "and": [
    { "math": [ "n_wm_upgrade_tier < 4" ] },
    { "math": [ "n_wm_xp >= (n_wm_upgrade_tier + 2)" ] }
  ]},
  "then": [
    { "math": [ "n_wm_xp = ..." ] },
    { "math": [ "n_wm_upgrade_tier = ..." ] },
    { "math": [ "u_wm_upgrade_result = 1" ] }      // 上書き: 成功
  ]
},

// 表示フェーズ: switch/case 内は結果コードの3-way if のみ
{ "switch": { "math": [ "u_wm_enhance_type" ] },
  "cases": [
    { "case": 1, "effect": [
      { "if": { "math": [ "u_wm_upgrade_result == 1" ] },
        "then": [ { "u_message": "...取得しました！", "type": "good" } ] },
      { "if": { "math": [ "u_wm_upgrade_result == 2" ] },
        "then": [ { "u_message": "...既に最大レベルです。", "type": "bad" } ] },
      { "if": { "math": [ "u_wm_upgrade_result == 3" ] },
        "then": [ { "u_message": "XPが不足しています。", "type": "bad" } ] }
    ] },
    // case 2-5: 同構造。メッセージ文字列のみ異なる
  ]
}
```

**結果コードの設計**:

| コード | 意味 | 設定タイミング |
|---|---|---|
| 1 | 成功 | XP支払い成功時（最後に上書き） |
| 2 | 最大レベル | ティア >= 4 チェック（デフォルトを上書き） |
| 3 | XP不足 | 初期値（デフォルト）。成功/最大のいずれにも該当しない場合 |

**動作原理**: CDDA の逐次実行保証により、デフォルト値（3）→ 最大チェック（2）→ 成功チェック（1）の順に上書きされる。成功チェックの `and` ガード（`n_wm_upgrade_tier < 4`）により、最大レベルの時に成功条件が誤って発火するのを防ぐ。

**利点**:

- 計算（複雑な条件分岐）と表示（固定文字列の3択）が完全に分離される
- 新しい強化タイプを追加する場合、case effect はメッセージ文字列の差し替えのみ
- switch/case 内のネストが 1段に統一され、可読性が向上

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — `wm_enhance_generic` の5 case を結果コードパターンで統一

## EOC 統合リファクタリングパターン

同一構造で変数名・メッセージのみ異なる複数の EOC を、**ルーティング変数 + 単一汎用 EOC** に統合するパターン。

### 適用条件

- 2つ以上の EOC が同一の if/else 構造を持つ
- 違いが変数名（`n_wm_buff_melee_damage` vs `n_wm_buff_melee_tohit`）とメッセージ文字列のみ
- カテゴリ制約（近接専用 / 遠隔専用 / 両方可）が異なる場合、outer gate で制御可能

### 統合手順

1. **ルーティング変数**を定義する（例: `u_wm_enhance_type` = 1〜5）
2. **talk_topic 側**で response `effect` を配列形式にし、`math` でルーティング変数を設定
3. **単一の汎用 EOC**（`wm_enhance_generic`）で if/else 連鎖による5-way分岐を実装
4. **カテゴリ outer gate**: ルーティング変数の値に応じた武器カテゴリチェックを if/else 連鎖の外側に配置

```jsonc
// wm_enhance_generic: 汎用強化ロジック
{
  "type": "effect_on_condition",
  "id": "wm_enhance_generic",
  "effect": [
    {
      // カテゴリ outer gate: type 1-3 → melee/supported, type 4-5 → ranged/supported
      "if": {
        "or": [
          { "and": [
            { "math": [ "u_wm_enhance_type <= 3" ] },
            { "or": [
              { "compare_string": [ "melee", { "npc_val": "wm_wcat" } ] },
              { "compare_string": [ "supported", { "npc_val": "wm_wcat" } ] }
            ]}
          ]},
          { "and": [
            { "math": [ "u_wm_enhance_type >= 4" ] },
            { "or": [
              { "compare_string": [ "ranged", { "npc_val": "wm_wcat" } ] },
              { "compare_string": [ "supported", { "npc_val": "wm_wcat" } ] }
            ]}
          ]}
        ]
      },
      "then": [
        // switch/case による値別ルーティング（case 0 はフォールバック。型ガードを使う代替パターンもあり）
        // 各分岐内では動的ティアアップグレードパターン（前述）を使う
        {
          "switch": { "math": [ "u_wm_enhance_type" ] },
          "cases": [
            { "case": 1, "effect": [ /* 変数: n_wm_buff_melee_damage, メッセージ: 近接ダメージ */ ] },
            { "case": 2, "effect": [ /* 変数: n_wm_buff_melee_tohit, メッセージ: 近接命中 */ ] },
            { "case": 3, "effect": [ /* ... */ ] },
            { "case": 4, "effect": [ /* ... */ ] },
            { "case": 5, "effect": [ /* ... */ ] },
            {
              "case": 0,
              "effect": [
                { "u_message": "内部エラー: 不明な強化タイプです。", "type": "bad" }
              ]
            }
          ]
        }
      ],
      "else": [
        { "u_message": "この武器ではこの強化は利用できません。", "type": "bad" }
      ]
    }
  ]
}
```

> **注**: talk_topic の response `condition` でカテゴリ制約が既にフィルタリングされている場合、この outer gate は除去し EOC を純粋な実行ロジックにできる。詳細は後続「カテゴリ outer gate の除去」節を参照。

### 防御的 else の必須ルール

if/else 連鎖で数値によるルーティングを行う場合、**連鎖の最末尾に未初期化値（`u_` 変数はデフォルト 0）を捕捉する防御的 else が必須**。

```jsonc
// 5-way if/else 連鎖の末尾
"else": {
  "if": { "math": [ "u_wm_enhance_type == 5" ] },
  "then": [ /* 5番目の処理 */ ],
  "else": [
    // 防御的 else: 値が 1〜5 のいずれでもない場合（未初期化=0 など）
    { "u_message": "内部エラー: 不明な強化タイプです。", "type": "bad" }
  ]
}
```

**理由**: talk_topic で必ず 1〜5 が設定されていても、EOC チェーンに到達する前に例外パス（別mod の干渉、テストコードからの直接呼び出し等）で 0 のまま到達する可能性を排除できない。メッセージを出さずに沈黙で全分岐をスキップするより、エラーメッセージで開発者に通知する方がデバッグ容易。

**switch/case の場合**: 上記と同等の保護は `case 0` で実現できる。しきい値マッチングでは switch 値が 1〜5 のとき case 0 もマッチするが、常に最大の case 値が優先されるため通常動作に影響しない。未初期化値（0）の場合のみ case 0 が選択される。詳細は「switch/case による条件分岐」セクションを参照。

### 型ガードによる代替

switch/case の前に型ガード（`if { "and": [ ">= 1", "<= 5" ] }`）を配置し、`else` でエラーメッセージを出すパターンもある。この場合、switch/case 内の `case 0` は不要（型ガードで捕捉済み）。

```jsonc
{
  "if": { "and": [
    { "math": [ "u_wm_enhance_type >= 1" ] },
    { "math": [ "u_wm_enhance_type <= 5" ] }
  ]},
  "then": [
    // switch/case は cases 1-5 のみ（case 0 不要）
    { "switch": { "math": [ "u_wm_enhance_type" ] }, "cases": [ ... ] }
  ],
  "else": [
    { "u_message": "内部エラー: 不明な強化タイプです。", "type": "bad" }
  ]
}
```

**使い分け**:
- **型ガード方式**: switch 前にチェック。switch 本体が簡潔になる。型ガードを通過した後の値の妥当性が保証される
- **case 0 方式**: しきい値マッチングに依存。switch 内にエラーハンドリングが局所化される

いずれの場合も、未初期化値（0）の到達に対する防御は必須。

### 統合の効果

| 指標 | 変更前 | 変更後 |
|---|---|---|
| EOC 数 | 10 (5 entry + 5 nested) | 2 (1 entry + 1 generic) |
| 重複コード | 5組の同一構造 | 単一の 5-way if/else |
| メンテナンス性 | 全EOCに修正が必要 | 1箇所の修正で全強化に反映 |
| リスク | 低（構造同一の保証がある場合） | — |

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — 20 EOC → 12 EOC。5つのエントリポイント + 5つのネスト EOC を `EOC_WM_GENERIC_ENHANCE` + `wm_enhance_generic` の2 EOC に統合。

### カテゴリ outer gate の除去: ダイアログ層フィルタリングとの役割分離

talk_topic の response に `condition` でカテゴリ制約（例: `u_wm_can_enh_melee_damage`）が既に定義されている場合、EOC 側で同じ制約を outer gate として重複検証する必要はない。**制約は入口（ダイアログ）で一元的に管理し、EOC は純粋な実行ロジックに徹する。**

```jsonc
// BEFORE: EOC が武器カテゴリを再検証（二重チェック）
{
  "id": "wm_enhance_generic",
  "effect": [{
    "if": { /* 近接/遠隔/両方のカテゴリ制約 outer gate */ },
    "then": [ /* 強化ロジック */ ],
    "else": [ { "u_message": "この武器ではこの強化は利用できません。", "type": "bad" } ]
  }]
}

// AFTER: EOC は型ガード（1〜5）のみ。カテゴリ制約は talk_topic の condition に委譲
{
  "id": "wm_enhance_generic",
  "effect": [{
    "if": { "and": [
      { "math": [ "u_wm_enhance_type >= 1" ] },
      { "math": [ "u_wm_enhance_type <= 5" ] }
    ]},
    "then": [ /* 強化ロジック — カテゴリチェックなし */ ],
    "else": [ { "u_message": "内部エラー: 不明な強化タイプです。", "type": "bad" } ]
  }]
}
```

**前提条件**:
- talk_topic の全 response に `condition` が定義され、EOC 到達前に不適格な選択肢がフィルタリングされていること
- `condition` で使われる変数（例: `u_wm_can_enh_*`）が `open_dialogue` より前に計算済みであること（`open_dialogue` と変数定義の順序を参照）

**利点**:
- EOC が武器カテゴリ（melee/ranged/supported）の知識を持たなくて済む
- カテゴリ追加時に EOC の修正が不要（talk_topic の condition のみ変更）
- 二重検証による不整合（EOC側とダイアログ側で制約が食い違う）のリスクがなくなる

**注意**: ダイアログを経由せず EOC が直接呼ばれる経路（例: `run_eocs` によるデバッグ呼び出し）がある場合、outer gate は必須。除去できるのは**全呼び出し経路がダイアログの condition フィルタリングを通過している**場合のみ。

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — `wm_enhance_generic` から武器カテゴリ outer gate を除去。カテゴリ制約は `EOC_WM_UPDATE_CAN_ENHANCE` → talk_topic response `condition` に集約。

### ラッパー EOC による呼び出し集約

複数の EOC の組み合わせを異なる経路（`run_eocs` と `u_run_inv_eocs` の `true_eocs`）から呼び出す場合、ラッパー EOC を作成して呼び出しを 1 箇所に集約する。EOC の追加・順序変更時に全呼び出し箇所を修正する手間を省ける。

```jsonc
// ラッパー EOC: UPDATE_COST + UPDATE_CAN_ENHANCE の組み合わせを集約
{
  "type": "effect_on_condition",
  "id": "EOC_WM_REFRESH_ENHANCE_STATE",
  "effect": [
    { "run_eocs": [ "EOC_WM_UPDATE_COST", "EOC_WM_UPDATE_CAN_ENHANCE" ] }
  ]
}

// 呼び出し元 A: EOC_WM_DIALOGUE_DETECT 内の run_eocs
{
  "id": "EOC_WM_DIALOGUE_DETECT",
  "effect": [
    { "run_eocs": "EOC_WM_REFRESH_ENHANCE_STATE" },
    { "open_dialogue": { "topic": "TALK_WM_ENHANCE" } }
  ]
}

// 呼び出し元 B: talk_topic response 内の u_run_inv_eocs
{
  "effect": [
    {
      "u_run_inv_eocs": "all",
      "search_data": [ { "wielded_only": true } ],
      "true_eocs": "EOC_WM_REFRESH_ENHANCE_STATE"
    }
  ]
}
```

**適用条件**:
- 同じ EOC の組み合わせが 2 箇所以上で使われている
- 呼び出し経路が異なる（`run_eocs` / `true_eocs` / `u_run_inv_eocs` 内の `run_eocs`）

**利点**:
- 組み合わせに変更があってもラッパー EOC 1 箇所の修正で済む
- 意味的なまとまりに名前が付き、コードの意図が明確になる
- `run_eocs` と `u_run_inv_eocs` の `true_eocs` の両方から同じラッパーを参照できる

**注意**: ラッパー EOC 内の `run_eocs` は talker コンテキストを継承する。`u_run_inv_eocs` の nested EOC として呼ばれる場合も、item を beta talker とするコンテキストがラッパー内の `run_eocs` に引き継がれるため、内部の EOC はアイテム変数（`n_`）にアクセスできる。

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — `EOC_WM_REFRESH_ENHANCE_STATE` が `EOC_WM_UPDATE_COST` + `EOC_WM_UPDATE_CAN_ENHANCE` をラップ。

## switch/case による条件分岐

複数の値による分岐（enum-like dispatch）を if/else チェーンの代わりに `switch`/`case` で実装できる。CDDA の switch/case は**しきい値マッチング**で動作する。

### マッチング動作

switch 値が case 値**以上**である全 case のうち、**最大**の case 値が選択される。

| switch値 | マッチする case | 選択される case |
|---|---|---|
| 0 | 0 | case 0 |
| 1 | 0, 1 | case 1（最大値） |
| 2 | 0, 1, 2 | case 2（最大値） |
| 3 | 0, 1, 2, 3 | case 3（最大値） |

**ポイント**: case 0 は switch 値が 1 以上のときもマッチするが、常に最大の case 値が勝つため干渉しない。この特性により case 0 をフォールバック（catch-all）として安全に使える。

### 基本構文

```jsonc
{
  "switch": { "math": [ "u_my_variable" ] },
  "cases": [
    {
      "case": 1,
      "effect": [
        // 値が1のときの処理
      ]
    },
    {
      "case": 2,
      "effect": [
        // 値が2のときの処理
      ]
    },
    {
      "case": 0,
      "effect": [
        { "u_message": "内部エラー: 不明な値です。", "type": "bad" }
      ]
    }
  ]
}
```

**構文上の注意**:
- `"effect"` フィールドには**必ず配列**を指定する。単一要素でも `[{...}]` でラップすること（配列内の if/then/else をネストさせるため）
- `"switch"` には `{ "math": [ "変数名" ] }` を指定する
- `"case"` は数値のみ。文字列は不可

### ネスト削減効果

if/else チェーンでは分岐の深さが値の数に比例して増加するが、switch/case ではネストが固定:

| 方式 | ネスト段数（5値分岐の場合） |
|---|---|
| if/else チェーン | 4段（if → if → if → if） |
| switch/case | 3段（if → switch case → if → if） |

### 使い分け

| シナリオ | 推奨 |
|---|---|
| 値が互いに排他的（enum-like） | switch/case |
| 条件が複雑で大小比較が混在 | if/else チェーン |
| 各分岐内で動的ティアアップグレードパターン（前述）を使う | switch/case（ネスト削減で読みやすくなる） |

### 防御的フォールバック

switch/case では case 0 を末尾に配置することで、if/else チェーンの「防御的 else」と同等の保護を実現できる。しきい値マッチングにより、switch 値が 1 以上のとき case 0 はマッチしても選択されず、0 のときだけ case 0 が発火する。

```jsonc
"cases": [
  { "case": 1, "effect": [ /* 通常処理 */ ] },
  { "case": 2, "effect": [ /* 通常処理 */ ] },
  { "case": 0, "effect": [
    { "u_message": "内部エラー: 不明な値です。", "type": "bad" }
  ]}
]
```

**注記**: 型ガード（`if` + 範囲チェック）を switch の前に配置する場合、`case 0` は省略可能。型ガードの `else` が未初期化値を捕捉するため。詳細は「防御的 else の必須ルール > 型ガードによる代替」を参照。

### 実績

- CDDA バニラ: vitrification, portal_storm, LIXA, labyrinth 等で広く使用
- `mods/small/wm_weapon_mastery/data/eoc.json` — 5つの強化タイプを switch/case に統合（ネスト 4段 → 3段）

## 文字列変数による条件分岐

`math` で使われる `n_` / `u_` 変数は**数値のみ**だが、CDDA には**文字列を保持できるコンテキスト変数**の仕組みがある。`u_run_inv_eocs` 内でアイテムにカテゴリ文字列を保存し、後続 EOC で条件分岐するパターン。

### 変数の設定

```json
// アイテム変数に文字列を保存（u_run_inv_eocs 内）
{ "npc_add_var": "wm_wcat", "value": "melee" }

// プレイヤー変数に文字列を保存
{ "u_add_var": "wm_last_action", "value": "enhance" }
```

`npc_add_var` は同じキーで複数回呼んでも**累積せず上書き**される。毎回初期値を設定してから条件付きで上書きするパターンが安全:

```json
{ "npc_add_var": "wm_wcat", "value": "unsupported" },    // デフォルト
{ "if": { "npc_has_flag": "WM_SUPPORTED" },
  "then": [ { "npc_add_var": "wm_wcat", "value": "supported" } ] }
```

### 条件分岐での利用

```json
{
  "if": { "compare_string": [ "melee", { "npc_val": "wm_wcat" } ] },
  "then": [ ... ]
}
```

### 複数値の OR 判定

```json
{
  "if": {
    "or": [
      { "compare_string": [ "melee", { "npc_val": "wm_wcat" } ] },
      { "compare_string": [ "supported", { "npc_val": "wm_wcat" } ] }
    ]
  },
  "then": [ ... ]
}
```

### 未定義変数との比較

未設定の変数は空文字列 `""` として扱われる:

```json
{ "compare_string": [ "", { "u_val": "some_var" } ] }
```

### 数値変数との使い分け

| 要件 | 方式 | 例 |
|---|---|---|
| 数値計算が必要（加算・乗算） | `math` (`n_`/`u_`) | `n_wm_xp = n_wm_xp + 1` |
| 条件分岐のみ | `npc_add_var` + `compare_string` | `npc_add_var: "wm_wcat", "melee"` |

文字列変数による分岐は値の意味が明確で読みやすいが、数値演算が必要な処理には使えない。

### 実績

- `external/cdda/data/mods/TEST_DATA/EOC.json` — `npc_add_var` のテストケース
- `external/cdda/data/mods/aftershock_exoplanet/` — `compare_string` の豊富な使用例（talk_topic 条件分岐、EOC 条件判定）
- `mods/small/wm_weapon_mastery/data/eoc.json` — `npc_add_var` + `compare_string` で武器カテゴリ判定を文字列化

## `copy_var` / `var_val` による動的変数参照

CDDA の `var_val` は変数名の文字列を解決して実変数にアクセスする二段階参照（double indirection）機構。`copy_var` と組み合わせることで、複数の case で重複するロジックをパラメータ化された単一ブロックに統合できる。

### 基本構文

`var_val` は context_val に格納された変数名文字列を以下のスコーププレフィックスで解決する:

| プレフィックス | 解決先 | 例: context_val の値 | アクセスされる変数 |
|---|---|---|---|
| `n_` | npc_val | `"n_wm_buff_melee_damage"` | `{ "npc_val": "wm_buff_melee_damage" }` |
| `u_` | u_val | `"u_wm_xp"` | `{ "u_val": "wm_xp" }` |
| `_` | context_val | `"_some_context"` | `{ "context_val": "some_context" }` |
| プレフィックスなし | global_val | `"global_var"` | `{ "global_val": "global_var" }` |

プレフィックスは **`set_string_var` で格納する文字列に含める**（`var_val` 自身ではプレフィックスを付与しない）。

### 操作用語

- **`set_string_var`**: 文字列を context_val / npc_val に格納する。第1引数は値となる文字列、`target_var` で格納先を指定
- **`context_val`**: コンテキスト変数。EOC 内では `run_eocs` を跨いで生存（コピー渡し）。dialogue effect 内で直接設定すれば dialogue セッション中は topic 跨ぎで永続。`var_val` の名前解決に使われる
- **`copy_var`**: source の変数値を target にコピーする。source / target_var は両方とも変数オブジェクト（`{ "npc_val": "..." }` 等）
- **`var_val`**: 変数オブジェクト内で使用。context_val の文字列を実変数名に解決する

### パターン: 複数 case の重複ロジック統合

**背景**: 5つの強化タイプ（近接ダメージ/命中/速度、遠隔ダメージ/精度）がそれぞれ異なるバフ変数（`n_wm_buff_melee_damage` 等）を持つが、アップグレードロジック（最大レベルチェック → XP チェック → コスト支払い → レベル増加）は全タイプ同一。

**解法**:

```jsonc
// Step 1: 型から変数名文字列を決定（context_val に格納）
{ "if": { "math": [ "u_wm_enhance_type == 1" ] },
  "then": [ { "set_string_var": "n_wm_buff_melee_damage",
               "target_var": { "context_val": "wm_upgrade_source" } } ] },
{ "if": { "math": [ "u_wm_enhance_type == 2" ] },
  "then": [ { "set_string_var": "n_wm_buff_melee_tohit",
               "target_var": { "context_val": "wm_upgrade_source" } } ] },
// ... type 3, 4, 5 も同様

// Step 2: var_val で動的読み出し → 汎用作業変数にコピー
{ "copy_var": { "var_val": "wm_upgrade_source" },
               "target_var": { "npc_val": "wm_upgrade_tier" } },

// Step 3: 汎用アップグレードロジック（n_wm_upgrade_tier に対して一度だけ）
{ "math": [ "u_wm_upgrade_result = 3" ] },
{ "if": { "math": [ "n_wm_upgrade_tier >= 4" ] },
  "then": [ { "math": [ "u_wm_upgrade_result = 2" ] } ] },
{ "if": { "and": [
    { "math": [ "n_wm_upgrade_tier < 4" ] },
    { "math": [ "n_wm_xp >= (n_wm_upgrade_tier + 2)" ] }
  ]},
  "then": [
    { "math": [ "n_wm_xp = n_wm_xp - (n_wm_upgrade_tier + 2)" ] },
    { "math": [ "n_wm_upgrade_tier = n_wm_upgrade_tier + 1" ] },
    { "math": [ "u_wm_upgrade_result = 1" ] }
  ]
},

// Step 4: var_val で動的書き戻し → 元のバフ変数に反映
{ "copy_var": { "npc_val": "wm_upgrade_tier" },
               "target_var": { "var_val": "wm_upgrade_source" } },

// Step 5: switch/case で結果表示（各 case は u_wm_upgrade_result のみ判定）
```

### 効果

| 指標 | Before | After |
|---|---|---|
| アップグレードロジックの重複 | 5組（各 case 内） | 1組（共有） |
| case あたりのネスト段数 | 3段（if → if/else → if/else） | 1段（result 別の3-way if） |
| ネスト総深度 | 5段 | 3段 |

### var_val の write 側制約

`copy_var` の `target_var` に `var_val` を使うパターンには CDDA エコシステム内での使用実績がない。**実装前に必ず小規模なテスト EOC で検証すること**（テストパターン: `set_string_var` でターゲット名を設定 → `copy_var` + `var_val` target → `u_message` で結果確認）。

テストが失敗する場合のフォールバック（Plan B）:
```jsonc
// 書き戻しを各 case 内で直接行う
// 共有ロジック（Step 2-3）は維持、Step 4 のみ分離
{ "case": 1, "effect": [
  { "copy_var": { "npc_val": "wm_upgrade_tier" },
                 "target_var": { "npc_val": "wm_buff_melee_damage" } },
  { "if": { "math": [ "u_wm_upgrade_result == 1" ] }, ... }
] }
```

### 実績

- `external/cdda/data/mods/TEST_DATA/EOC.json:776-793` — `copy_var` + `var_val` source の全スコープテスト
- `mods/small/wm_weapon_mastery/data/eoc.json` — 5-to-1 コード統合（~90行削減）

## context_val によるメッセージ文字列の動的生成

`set_string_var` でコンテキスト変数に表示用文字列を格納し、`<context_val:>` タグでメッセージに埋め込むことで、switch/case によるメッセージ分岐を排除できる。

### 問題: switch/case によるメッセージの重複

結果コードパターン（前述「結果コードによる計算/表示の分離」）では、各 case 内に同じ構造のメッセージブロック（成功/最大/不足の 3-way if）が繰り返される。メッセージ文字列だけが異なる。

```jsonc
// switch/case による表示（5 case × 3 if = 15ブロックの重複）
{ "switch": { "math": [ "u_wm_enhance_type" ] },
  "cases": [
    { "case": 1, "effect": [
      { "if": { "math": [ "u_wm_upgrade_result == 1" ] },
        "then": [ { "u_message": "近接ダメージ強化 Tier ... を取得しました！", "type": "good" } ] },
      { "if": { "math": [ "u_wm_upgrade_result == 2" ] },
        "then": [ { "u_message": "近接ダメージは既に最大レベルです。", "type": "bad" } ] },
      { "if": { "math": [ "u_wm_upgrade_result == 3" ] },
        "then": [ { "u_message": "XPが不足しています。", "type": "bad" } ] }
    ]},
    // case 2-5: 同構造。メッセージ文字列のみ異なる（近接命中/攻撃速度/遠隔ダメ/遠隔精度）
  ]
}
```

### 解決策: set_string_var + <context_val:> でメッセージを動的化

switch/case で型別にメッセージ文字列を用意する代わりに、各型分岐で `set_string_var` によりコンテキスト変数にメッセージ用文字列を格納する。メッセージ表示は型によらず共通の 1 ブロックのみ。

```jsonc
// Step 1: 型判定 → context_val に表示名を格納（switch/case 不要）
{ "if": { "math": [ "u_wm_enhance_type == 1" ] },
  "then": [
    { "set_string_var": "近接ダメージ強化", "target_var": { "context_val": "upgrade_type"} }
  ]},
{ "if": { "math": [ "u_wm_enhance_type == 2" ] },
  "then": [
    { "set_string_var": "近接命中強化", "target_var": { "context_val": "upgrade_type"} }
  ]},
// ... type 3, 4, 5 も同様

// Step 2: 表示 — 全型で共通の 3-way if（1ブロックのみ）
{ "if": { "math": [ "u_wm_upgrade_result == 1" ] },
  "then": [ { "u_message": "<context_val:upgrade_type> Tier <npc_val:wm_upgrade_tier> を取得しました！", "type": "good" } ] },
{ "if": { "math": [ "u_wm_upgrade_result == 2" ] },
  "then": [ { "u_message": "<context_val:upgrade_type>は既に最大レベルです。", "type": "bad" } ] },
{ "if": { "math": [ "u_wm_upgrade_result == 3" ] },
  "then": [ { "u_message": "XPが不足しています。 (現在XP: <npc_val:wm_xp>)", "type": "bad" } ] }
```

### 効果

| 指標 | Before (switch/case + 3-way if) | After (context_val + 3-way if) |
|---|---|---|
| メッセージブロック数 | 5 case × 3 if = 15 | 1 × 3 if = 3 |
| ネスト段数 | 3段（switch → case → if） | 2段（if/else チェーン → if） |
| 型追加時の変更箇所 | case effect 全体を複製（10行） | set_string_var 1行 + メッセージ文字列 |

### context_val の寿命とスコープ

#### EOC 内スコープ

`context_val` は EOC 実行中に有効。`run_eocs` で別 EOC を呼ぶと、呼出元の `context_val` は**コピー**されて callee に渡る。callee 側での書き換えは caller 側に伝播しない。

```jsonc
// CALLER: context_val を設定
{ "set_string_var": "original", "target_var": { "context_val": "my_var" } },
{ "run_eocs": "EOC_CALLEE" },
// ここでの my_var は "original" のまま（callee の変更は伝播しない）
{ "u_message": "<context_val:my_var>" }  // → "original"
```

明示的に変数を渡すには `run_eocs` の `"variables"` パラメータを使う:

```jsonc
{
  "run_eocs": "EOC_CALLEE",
  "variables": { "passed_key": "passed_value" }
}
// callee 側で { "context_val": "passed_key" } で読み取り可能
```

`run_eocs` + `variables` の構文は**フラットな兄弟構造**であり、入れ子オブジェクトは不可:

```jsonc
// 正しい
{ "run_eocs": "EOC_ID", "variables": { "key": "value" } }

// 誤り（"variables" が認識されない）
{ "run_eocs": { "id": "EOC_ID", "variables": { "key": "value" } } }
```

#### Dialogue 内スコープ

`context_val` の dialogue 内での挙動は設定方法によって異なる:

| 設定方法 | topic 遷移後の生存 | 備考 |
|---------|-------------------|------|
| talk_topic の `effect` 内で `set_string_var` を**直接**発行 | **生存する** | dialogue セッション中は複数 topic 跨ぎで永続 |
| talk_topic の `effect` → `run_eocs` → EOC 内で設定 | **消失する** | EOC コンテキストと dialogue コンテキストは別 |
| EOC 内で設定 → `open_dialogue` | **消失する** | `open_dialogue` は新規 dialogue コンテキストを作成 |
| dialogue を閉じる | **全クリア** | セッション終了で破棄 |

```jsonc
// 生存するパターン: effect 内で直接 set_string_var
{
  "text": "実行",
  "effect": [
    { "set_string_var": "value", "target_var": { "context_val": "my_var" } }
  ],
  "topic": "TALK_DISPLAY"  // 遷移先でも <context_val:my_var> で表示可能
}

// 消失するパターン: run_eocs 経由
{
  "text": "実行",
  "effect": [ { "run_eocs": "EOC_SETTER" } ],  // EOC_SETTER 内で context_val 設定
  "topic": "TALK_DISPLAY"  // context_val は表示されない
}
```

#### `<context_val:>` タグの対応状況

| コンテキスト | 動作 | 実績 |
|-------------|------|------|
| EOC の `u_message` | **対応** | `wm_weapon_mastery` で使用実績あり |
| talk_topic の `dynamic_line` | **対応** | effect 直接設定で生存する場合のみ表示可能 |

#### `copy_var` の注意点

存在しない `context_val` を `copy_var` の source に指定すると、代入先の変数が不正な状態になり、後続の `u_message` が切り捨てられる。`context_val` の値を `u_message` で表示したいだけの場合は、`copy_var` で `u_val` に中継せず `<context_val:>` タグを直接使うこと。

```jsonc
// 非推奨: 存在しない context_val を copy_var すると u_message が破綻
{ "copy_var": { "context_val": "may_not_exist" }, "target_var": { "u_val": "bk" } },
{ "u_message": "value: <u_val:bk>" }  // ← 後続文字列が切り捨てられる

// 推奨: <context_val:> タグを直接使う
{ "u_message": "value: <context_val:may_not_exist>" }  // 存在しなければ空表示
```

### 実績
`mods/small/wm_weapon_mastery/data/eoc.json` — `wm_enhance_generic` で switch/case メッセージブロックを全廃。5型 × 3メッセージの重複を context_val 3メッセージに統合。

## 参照先

- ドキュメント: `external/cdda/doc/JSON/EFFECT_ON_CONDITION.md`
- 実装例:
  - `external/cdda/data/mods/BombasticPerks/perkdata/empath.json` — EVENT 型 EOC
  - `external/cdda/data/mods/Perk_melee/EOC/leveling.json` — math + character_kills_monster
  - `external/cdda/data/mods/TEST_DATA/EOC.json` — u_run_inv_eocs のテストケース
  - `external/cdda/data/json/effects_on_condition/` — バニラ EOC
