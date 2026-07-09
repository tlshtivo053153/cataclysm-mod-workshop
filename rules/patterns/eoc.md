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

## `character_kills_monster` イベントの注意点

- `character_kills_monster` は**プレイヤー・NPC を問わず**全キャラクターで発火する
- avatar のみに限定するには `"condition": "u_is_avatar"` を使用する

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
- **`n_` 変数は enchantment の math 式から直接アクセス不可。** enchantment の math はキャラクターコンテキスト（`u_`）で評価されるため、アイテム変数を参照したい場合は EOC で `n_` → `u_` にコピーしてから effect を付与する（`rules/patterns/enchantment.md` の「変数スコープの制約」参照）
- **`u_` 変数は `u_run_inv_eocs` 内から読み取り可能。** talk_topic や親EOCで設定した `u_` math 変数は、`u_run_inv_eocs` の nested EOC（アイテムスコープ）内でも `u_` プレフィックスでアクセス可能。CDDA 公式ドキュメント（`EFFECT_ON_CONDITION.md`）で `u_run_inv_eocs` はデュアルトーカーモデルを維持し、alpha talker（`u_`）はキャラクターのまま、beta talker（`n_`）にアイテムが割り当てられると明記されている。両スコープが同時にアクセス可能であり、math 変数の `u_` プレフィックスは常に alpha talker にスコープされる（`NPCs.md`）。実績: `wm_apply_buffs` が既に `u_run_inv_eocs` 内で `u_` math 変数への書き込みを行っている。

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

### EOC から talk_topic へ遷移した後の戻り先制御

`open_dialogue` で対話を開いた後、結果ページ（TALK_RESULT）から元の対話に戻る必要がある場合、**`u_` 変数に戻り先を記録**するパターンを使う。

```json
// 対話を開く前に u_ 変数で戻り先をマーク
{ "math": [ "u_wm_last_dialogue = 1" ] },
{ "open_dialogue": { "topic": "TALK_WM_ENHANCE_MELEE" } }

// TALK_RESULT の「続ける」選択肢で呼ばれる EOC:
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

### talk_topic 応答からの EOC 呼び出し

talk_topic の response から EOC を実行するには `"effect"` フィールドに `"run_eocs"` を指定する。

```json
{
  "type": "talk_topic",
  "id": "TALK_WM_ENHANCE_MELEE",
  "dynamic_line": "強化項目を選んでください。",
  "responses": [
    {
      "text": "近接ダメージ強化",
      "topic": "TALK_WM_RESULT",
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

### `dynamic_line` での `u_` 変数表示: `n_` → `u_` コピー + `<u_val:>` パターン

talk_topic の `dynamic_line` では `<u_val:変数名>` でプレイヤー変数の値を直接表示できる。アイテム変数（`n_`）を `dynamic_line` に表示したい場合は、対話を開く**前に**アイテム変数をプレイヤー変数にコピーする。

```jsonc
// EOC_WM_OPEN_DIALOGUE: 対話を開く前に wm_update_effects を実行
// wm_update_effects → wm_apply_buffs が n_ → u_ コピーを行う
{
  "type": "effect_on_condition",
  "id": "EOC_WM_OPEN_DIALOGUE",
  "effect": [
    { "run_eocs": "wm_update_effects" },  // ★ 事前に u_ 変数を同期
    {
      "u_run_inv_eocs": "all",
      "search_data": [ { "wielded_only": true } ],
      "true_eocs": [ "wm_detect_category", "wm_open_dialogue_detect" ]
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
  "id": "TALK_WM_ENHANCE_MELEE",
  "dynamic_line": "近接ダメージ: Tier <u_val:wm_melee_damage>/4\n保有XP: <u_val:wm_xp>"
}
```

**注意点:**
- `<u_val:>` は math 変数（`u_xxx`）の**数値**をそのまま表示する。文字列変数（`u_add_var` で設定）も表示可能
- 未定義の変数は `0` として表示される
- `u_run_inv_eocs` で複数アイテムを処理すると最後のアイテムの値だけが残るため、`wielded_only: true` で wield 中の武器だけに限定する
- `dynamic_line` 内の `"math"` 条件（`{ "math": [...], "yes": "...", "no": "..." }`）では `&&` / `||` が使えず、`"and"` / `"or"` も利用不可。値の範囲チェックが必要な場合は `<u_val:>` で直接数値表示する方が簡潔

**実績**: `mods/small/wm_weapon_mastery/data/talk_topics.json` — 3つの talk_topic で `<u_val:>` を使用したバフ状態表示

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
        // 5-way if/else chain: enhance_type == 1 → ... == 2 → ... == 5
        // 各分岐内では動的ティアアップグレードパターン（前述）を使う
        {
          "if": { "math": [ "u_wm_enhance_type == 1" ] },
          "then": [ /* 変数: n_wm_buff_melee_damage, メッセージ: 近接ダメージ */ ],
          "else": {
            "if": { "math": [ "u_wm_enhance_type == 2" ] },
            "then": [ /* 変数: n_wm_buff_melee_tohit, メッセージ: 近接命中 */ ],
            "else": {
              // ... 3, 4, 5 と続く
              "else": [
                { "u_message": "内部エラー: 不明な強化タイプです。", "type": "bad" }
              ]
            }
          }
        }
      ],
      "else": [
        { "u_message": "この武器ではこの強化は利用できません。", "type": "bad" }
      ]
    }
  ]
}
```

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

### 統合の効果

| 指標 | 変更前 | 変更後 |
|---|---|---|
| EOC 数 | 10 (5 entry + 5 nested) | 2 (1 entry + 1 generic) |
| 重複コード | 5組の同一構造 | 単一の 5-way if/else |
| メンテナンス性 | 全EOCに修正が必要 | 1箇所の修正で全強化に反映 |
| リスク | 低（構造同一の保証がある場合） | — |

**実績**: `mods/small/wm_weapon_mastery/data/eoc.json` — 20 EOC → 12 EOC。5つのエントリポイント + 5つのネスト EOC を `EOC_WM_GENERIC_ENHANCE` + `wm_enhance_generic` の2 EOC に統合。

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

## 参照先

- ドキュメント: `external/cdda/doc/JSON/EFFECT_ON_CONDITION.md`
- 実装例:
  - `external/cdda/data/mods/BombasticPerks/perkdata/empath.json` — EVENT 型 EOC
  - `external/cdda/data/mods/Perk_melee/EOC/leveling.json` — math + character_kills_monster
  - `external/cdda/data/mods/TEST_DATA/EOC.json` — u_run_inv_eocs のテストケース
  - `external/cdda/data/json/effects_on_condition/` — バニラ EOC
