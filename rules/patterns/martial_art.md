# 格闘スタイル (martial_art) 実装パターン

CDDAに新規の格闘スタイル（martial art）を追加するためのパターンファイル。

## ファイル構成

小規模な格闘スタイルmod（テクニック2〜4種、バフ1〜2種）の最小構成：

| ファイル | type | 内容 |
|---|---|---|
| `modinfo.json` | `MOD_INFO` | mod登録情報。`category: "misc"` 推奨 |
| `data/martialarts.json` | `martial_art` | 格闘スタイル定義 + インラインバフ |
| `data/techniques.json` | `technique` | テクニック定義 |

バフは別ファイルではなく、`martial_art` の `static_buffs` / `onmove_buffs` / `onpause_buffs` 配列内にインラインで定義する。

## 参照ファイル（external/cdda/）

| ファイル | 目的 |
|---|---|
| `data/json/martialarts.json` | 既存スタイルの構造確認（bojutsu, barbaran, eskrima 等） |
| `data/json/techniques.json` | テクニック構造の確認（bojutsu系, eskrima系等） |
| `data/json/weapon_categories.json` | 武器カテゴリ定義と所属武器の確認 |
| `doc/JSON/MARTIALART_JSON.md` | martial_art 型の全フィールドリファレンス |

## フィールド使用ルール

### `attack_vectors`（テクニック）

**武器限定テクニックでは `["vector_null"]` が必須。** `vector_null` を指定することで、ゲームは装備中の武器から攻撃部位を解決する。

```json
"attack_vectors": [ "vector_null" ]
```

- `vector_null` を省略した場合、素手テクニック扱いになり、`strictly_melee: true` のスタイルでは発動しない
- `vector_punch` は素手限定。武器テクニックには使わない
- すべての bojutsu / sojutsu 系テクニックが `vector_null` を使用している

### `skill_requirements`（テクニック）

**武器テクニックの `skill_requirements` は常に `"melee"` を使用する。** 特定の武器スキル（`"bashing"`, `"cutting"` 等）ではない。

```json
"skill_requirements": [ { "name": "melee", "level": 3 } ]
```

- `primary_skill`（スタイル側）がスケーリングを制御するが、テクニックのアンロック判定は汎用 `melee` スキルを使用する
- すべての bojutsu, eskrima, barbaran テクニックが `"melee"` 指定
- `"bashing"` を指定すると、そのテクニックが発動しなくなる可能性が高い

### `arm_block`

**`arm_block` は常に unarmed スキルで判定される。** スタイルの `primary_skill` には依存しない。

```json
"arm_block": 1
```

- 値 `1` は unarmed 1 でアームブロック可能を意味する（バニラの boxing が使用）
- `primary_skill: "bashing"` の strictly_melee スタイルでも、arm_block の判定は unarmed スキル固定で行われるため問題なく発動する

### `teachable`

**`teachable` はデフォルトで `true` のため、明示的に指定しない。** バニラの実戦スタイルはすべてこのフィールドを省略している。

- `teachable: true` を明示しても動作するが、バニラの慣例に反する
- `teachable: false` は `style_none` と `style_kicks` の2つの疑似スタイルのみが使用

### `mult_bonuses`（テクニック・バフ共通）

**`mult_bonuses` は単一の配列。damage と movecost は同じ配列内に並べる。**

```json
"mult_bonuses": [
  { "stat": "damage", "type": "bash", "scale": 1.25 },
  { "stat": "movecost", "scale": 1.2 }
]
```

- `mult_bonuses` がサポートする stat は `damage` と `movecost` のみ（MARTIALART_JSON.md 参照）
- damage 指定時は `"type": "bash"`（または `"cut"`, `"stab"`）が必要
- movecost は `type` 不要。`scale: 0.7` で30%高速化、`scale: 1.2` で20%低速化

### `autolearn`

**`autolearn` の形式は `[["skill_name", level]]`。** 整数でレベルを指定する。

```json
"autolearn": [ [ "bashing", 4 ] ]
```

- brawling の例: `"autolearn": [ [ "melee", 1 ] ]`

### `strictly_melee`

**武器限定の格闘スタイルでは `"strictly_melee": true` が必須。** これを指定しないと、素手でもスタイルのテクニックやバフが発動してしまう。

```json
{
  "type": "martial_art",
  "id": "style_my_style",
  "name": "My Style",
  "description": "A weapon-based martial art.",
  "primary_skill": "bashing",
  "strictly_melee": true,
  "weapon_category": [ "BATONS" ],
  ...
}
```

- 素手と武器の両方に対応するスタイル（brawling, judo 等）は `strictly_melee` を指定しない
- `strictly_melee: true` のスタイルでは、テクニックに `attack_vectors: ["vector_null"]` が必須（武器から攻撃部位を解決するため）

## 武器カテゴリ検証

**実装前に必ず、指定した `weapon_category` に実際に属する武器を確認する。** 武器名から直感的に判断すると間違えることがある。

- `bat`（baseball bat）→ `MACES` カテゴリ。`BATONS` ではない
- `baton` → `BATONS` カテゴリ
- 確認方法:
  ```bash
  rg "weapon_category.*BATONS" external/cdda/data/json/items/melee/
  ```

主要な BATONS 武器: `baton`, `baton-extended`, `crowbar`, `pipe`, `nail bat`, `shillelagh`, `PR24-retracted`, `cudgel`, `tonfa`

## バフ定義

バフは `martial_art` 定義内の配列にインラインで定義し、以下の3種類がある：

| バフ種類 | 配列フィールド | 発動条件 |
|---|---|---|
| static_buffs | `static_buffs` | 常時発動 |
| onmove_buffs | `onmove_buffs` | 移動時発動（`buff_duration` 必須） |
| onpause_buffs | `onpause_buffs` | 待機時発動（`buff_duration` 必須） |

```json
"static_buffs": [
  {
    "id": "buff_my_style_static",
    "name": "Buff Name",
    "description": "Description.\n\n+10% bash damage.",
    "melee_allowed": true,
    "mult_bonuses": [ { "stat": "damage", "type": "bash", "scale": 1.1 } ]
  }
]
```

- バフの `id` は `buff_` プレフィックスを使用（`buff_scrap_striker_static` 等）
- バフは独立した `type` オブジェクトではなく、martial_art 定義に埋め込む

## テクニック定義の注意点

- `melee_allowed: true` は武器テクニックに必須。`unarmed_allowed` は不要
- テクニック `id` は `tec_` プレフィックスを使用（`tec_scrap_striker_smash` 等）
- メッセージは2要素配列: `[ "プレイヤー用", "NPC用" ]`

## テクニックテンプレート

### ダメージ重視型（スキル要件なし、常時発動）

```json
{
  "type": "technique",
  "id": "tec_my_smash",
  "name": "Technique Name",
  "messages": [
    "You smash %s with a brutal blow",
    "<npcname> smashes %s with a brutal blow"
  ],
  "melee_allowed": true,
  "mult_bonuses": [
    { "stat": "damage", "type": "bash", "scale": 1.25 },
    { "stat": "movecost", "scale": 1.2 }
  ],
  "attack_vectors": [ "vector_null" ]
}
```

### 速度重視型（スキル要件あり）

```json
{
  "type": "technique",
  "id": "tec_my_quick",
  "name": "Quick Strike",
  "messages": [
    "You strike %s with a quick swing",
    "<npcname> strikes %s with a quick swing"
  ],
  "skill_requirements": [ { "name": "melee", "level": 3 } ],
  "melee_allowed": true,
  "mult_bonuses": [
    { "stat": "movecost", "scale": 0.7 },
    { "stat": "damage", "type": "bash", "scale": 0.8 }
  ],
  "attack_vectors": [ "vector_null" ]
}
```

## よくある間違い

1. `skill_requirements` に `"bashing"` を指定する → `"melee"` に修正
2. `attack_vectors` を省略する → `["vector_null"]` を追加
3. `teachable: true` を明示する → 削除
4. `mult_bonuses` を分割して2つの配列にする → 1つの配列に統合
5. `bat` を BATONS 武器と誤認する → weapon_categories.json で実在確認

## modinfo.json の category

格闘スタイルmodの `category` は `"misc"` を使用する。CDDA スキーマに `"martial_arts"` カテゴリは存在しない。

```json
{
  "type": "MOD_INFO",
  "id": "my_martial_art",
  "name": "My Martial Art",
  "description": "Adds a new martial art style.",
  "category": "misc",
  "dependencies": [ "dda" ],
  "version": "1.0"
}
```
