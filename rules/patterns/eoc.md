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

## `character_kills_monster` イベントの注意点

- `character_kills_monster` は**プレイヤー・NPC を問わず**全キャラクターで発火する
- 0.I RC では avatar のみに限定する `u_is_avatar` 条件が使えないため、全キャラクター対象になることを前提に設計する
- 代替フィルターが必要な場合: `u_has_trait` で特定の mutation/trait を持つキャラクターのみに限定する

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

## message 内の変数埋め込み

```json
{ "u_message": "<npc_val:wm_xp>", "type": "info" }
```

- `<global_val:変数名>` — グローバル変数
- `<context_val:変数名>` — イベントコンテキスト変数
- `<npc_val:変数名>` — NPC/アイテム変数（`u_run_inv_eocs` 内でのみ意味を持つ）
- **未定義変数のタグが正しく置換されるかは実機確認が必要**（空文字列になる可能性がある）

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

## 参照先

- ドキュメント: `external/cdda/doc/JSON/EFFECT_ON_CONDITION.md`
- 実装例:
  - `external/cdda/data/mods/BombasticPerks/perkdata/empath.json` — EVENT 型 EOC
  - `external/cdda/data/mods/Perk_melee/EOC/leveling.json` — math + character_kills_monster
  - `external/cdda/data/mods/TEST_DATA/EOC.json` — u_run_inv_eocs のテストケース
  - `external/cdda/data/json/effects_on_condition/` — バニラ EOC
