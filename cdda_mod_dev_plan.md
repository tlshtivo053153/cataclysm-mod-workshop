# Cataclysm: DDA Mod開発計画 — AIエージェント活用ガイド

## プロジェクト概要

AIエージェントを用いてCataclysm: DDAのmodを開発し、ノウハウを蓄積することで、性能の低いモデルでもmod開発できる環境を構築する。

### 目標
- 小規模modの作成と旧modの新バージョン対応からスタート
- ノウハウ蓄積後に中規模・大規模modへ展開
- ルールの継続的強化

### 使用エージェント

| エージェント | 役割 | 制限 |
|---|---|---|
| Kilo Code | 設計・実装（高性能タスク） | — |
| OpenCode | 実装支援・コードレビュー | — |
| Qwen Code | ルール評価・検証 | 1000 RPD/日（無料） |
| Gemini CLI | ルール評価・検証 | 200〜300 RPD/日（無料） |

---

## ターゲットCDDAバージョン

### バージョン状況（2026年4月時点）

| 種別 | バージョン | 備考 |
|---|---|---|
| 安定版 | 0.H "Herbert" | 2025年8月リリース |
| **ターゲット（推奨）** | **0.I RC** | 仕様固定済み。バグ修正のみ |
| 実験的ビルド | experimental 2026-04-xx | 毎日更新。破壊的変更あり |

**本プロジェクトは 0.I RC をターゲットとする。**
実験的ビルドへの対応は `version_diff.md` に記録しながら後続フェーズで対応する。

### CDDAソースの配置

```
cdda-mod-dev/
└── external/
    └── cdda/               ← ここにCDDAのファイルを配置
        ├── data/
        │   ├── json/       ← コアゲームデータ（modの参考元）
        │   │   ├── items/
        │   │   ├── monsters/
        │   │   └── recipes/
        │   └── mods/       ← 同梱modのサンプル（MODDING.md参照）
        ├── doc/
        │   ├── MODDING.md  ← mod開発の公式ガイド（必読）
        │   └── JSON/
        │       └── JSON_INFO.md  ← 全JSONフィールドのリファレンス
        └── LICENSE
```

#### external/cdda/ の使い方

- `external/cdda/data/json/` を参照してアイテムIDやフラグの正確な綴りを確認する
- `external/cdda/data/mods/` の同梱modをサンプルとして読む
- `external/cdda/doc/JSON/JSON_INFO.md` を全JSONフィールドのリファレンスとして使う
- **エージェントへの指示例:**
  ```
  external/cdda/data/json/items/melee.json を参照して、
  近接武器の必須フィールドを確認してから実装してください。
  ```

> **注意:** `external/cdda/` はGit管理から除外する（`.gitignore` に追記）。
> CDDAのバージョンアップ時はこのディレクトリを差し替えて `version_diff.md` を更新する。

---

## 開発原則

- **設計・計画を先に行い、その後に実装を開始する**
- 高性能モデルで開発した後にルールを作る
- 低性能モデルでルールを評価する
- 問題が発生した場合は必ずログを残す
- `external/cdda/` のソースを常に参照して命名・構造の正確性を担保する
- **短期戦略（フェーズ1-2）と長期戦略（フェーズ3以降）を明確に分離する**

---

## フェーズ構成

### フェーズ1 — 小規模mod / 旧mod移植（最短突破ルート）

**完了条件:** 以下をすべて満たすこと
- [ ] 小規模mod（アイテム追加など）を1本、エラーなしで動作させる
- [ ] 旧modを1本、0.I RCで動作するよう移植する
- [ ] 発生したエラーをすべてログ化し `common_errors.md` に反映する
- [ ] `CORE.md` に10件以上のルールが記載されている

**作成順序（難易度順）:**
1. 旧modの移植 — バージョン差分の学習に最適。エラーメッセージがそのままルールになる
2. 単純アイテム追加mod — 武器・食料1〜3種類。JSON構造の基礎習得
3. 簡単なレシピ追加 — 既存アイテムのクラフトレシピ追加

### フェーズ2 — ルール評価サイクル（最短突破）

**最短突破戦略:**
- 1つの超単純mod（アイテム1個、copy-fromあり）を使う
- 「頻出エラーTOP3だけ」潰す（完璧主義禁止）
- 「条件付き合格」をOKにする（1〜2修正で直る = 合格）

**完了条件:** 以下をすべて満たすこと
- [ ] Qwen がルールファイル（`CORE.md` + `hints_basic.md`）のみを参照して、同じmodを**30回中24回以上**実装できる（成功率80%以上、誤差±9%程度）
- [ ] 軽微修正OKの成功率80%以上達成
- [ ] 失敗原因を `common_errors.md` に記録済み

> **重要:** フェーズ2では「汎化」はまだ気にしない。same-mod評価のみで80%達成を目指す。

> **なぜ30回か:** n=10では二項分布の信頼区間が広すぎる（真の成功率80%でも8/10を下回る確率が約38%）。n=30（24/30 = 80%）で誤差を±9%程度に抑え、フェーズ突破判定の信頼性を確保する。Qwen無料枠（1000 RPD/日）で十分実施可能。

**サイクル詳細（Day 3-6）:**

| Day | やること | ループ |
|---|---|---|
| Day 3 朝 | Qwen 1-5回目実行 | 各回毎に成功率確認 |
| Day 3 昼 | エラーTOP3分析 | 頻出エラーを抽出 |
| Day 3 夕 | hints_basic.md 更新 | TOP3のみ |
| Day 4 朝 | Qwen 6-15回目実行 | 改善確認（中間集計） |
| Day 4 昼 | 再度分析・更新 | 収束確認 |
| Day 5 朝 | Qwen 16-25回目実行 | 継続改善 |
| Day 5 夕 | Qwen 26-30回目実行 | 最終集計 |
| Day 6 | フェーズ2完了判定 | final（24/30以上で突破） |

**rule/capability 判定の実行タイミング:**

```
フェーズ2突破後（Day 5以降）に実施:

1. フェーズ2で失敗したタスクを確認
2. 高性能モデル(Kilo Code)で同じタスクを再実装
3. 高性能モデルも失敗 → rule起因 → ルールに追加
4. 高性能モデルは成功 → capability起因 → 委譲リストに追加
```

> **Note:** フェーズ2途中は判定しない。成功率80%達成が最優先。

### フェーズ3 — 中・大規模mod（長期戦略）

**フェーズ2完了後に移行**

**完了条件:** 以下をすべて満たすこと
- [ ] unseenタスクで80%以上成功
- [ ] ルール構造化が済んでいる
- [ ] human reviewポイントが明確

---

## ディレクトリ構造

```
cdda-mod-dev/
├── external/
│   └── cdda/               ← CDDAのソースファイル（gitignore対象）
├── rules/                  ← ノウハウ蓄積の核心
│   ├── CORE.md             ← 基本ルール（全モデル必読）
│   ├── hints_basic.md      ← 低性能モデル向け補足（冗長な説明・具体例）
│   ├── hints_advanced.md   ← 高性能モデル向け補足（設計判断・トレードオフ）
│   ├── json_schema.md      ← CDDAのJSONフォーマット仕様
│   ├── version_diff.md     ← バージョン差分（0.G→0.H→0.I等）
│   ├── common_errors.md    ← よくあるエラーと解決策
│   └── patterns/
│       ├── items.md
│       ├── monsters.md
│       └── scenarios.md
├── mods/
│   ├── seen/              ← 学習済みmod（フェーズ2用）
│   ├── unseen/           ← 未知タスク（フェーズ3用）
│   ├── small/            ← フェーズ1: 小規模mod
│   ├── medium/           ← フェーズ3: 中規模mod
│   └── large/            ← フェーズ3: 大規模mod
├── benchmarks/
│   ├── seen/            ← 学習、評価兼用
│   ├── unseen/          ← 評価専用（ルール更新に使用禁止）
│   └── random/          ← ランダム生成課題
├── logs/
│   ├── errors/          ← エラーログ（YYYY-MM-DD_mod名_エージェント名.md）
│   ├── agent_reports/   ← ルール評価レポート
│   └── summarized/       ← 集約ログ（AI生成）
├── scripts/
│   └── validate.sh       ← JSONバリデーションスクリプト
├── templates/
│   ├── modinfo.json     ← modinfo.jsonのテンプレート
│   └── design_template.md ← 設計書テンプレート
└── .gitignore
```

### .gitignore

```
external/cdda/
logs/
benchmarks/unseen/
*.swp
```

---

## テストレベル構造

### Level1: JSON構文OK
- `python3 -m json.tool` が通る
- 基本的なJSON構造が正しい

### Level2: 起動OK
- CDDAがmodを認識する
- エラーなしでゲームが起動する

### Level3: 意図通り動作（必須）
- 追加コンテンツが正しくスポーンする
- レシピが実際にクラフトできる
- バランスが崩壊していない

> **重要:** フェーズ2ではLevel2までの合格でOK。フェーズ3以降でLevel3を必須とする。

#### Level3 自動化方針（フェーズ3移行前に整備）

Level3は現状すべて手動であり、フェーズ3でunseenタスクが増えるとボトルネックになる。
以下の段階的な自動化を**フェーズ3移行前**に検討・整備すること。

| ステップ | 内容 | 難易度 |
|---|---|---|
| Step A | CDDAの `--lab` / `--json` オプション等でヘッドレス起動可否を調査 | 低 |
| Step B | 起動ログ（`debug.log`）のパースでスポーンエラーを自動検出 | 低 |
| Step C | Lua/Python スクリプトでデバッグメニュー操作を自動化（CDDA版テストドライバ） | 高 |

**短期的な妥協案（Step A/B のみで対応）:**
CDDAは `--mapsize` や `--loglevel debug` フラグで詳細ログを出力できる。起動ログに `unknown type` や `missing field` が含まれないこと＋アイテムIDが正常にパースされることを確認するだけでも Level3 の一部を代替できる。完全な動作確認（クラフト・スポーン）は週次の手動レビューで補う。

---

## ベンチマーク構造

### seen/unseen分離

```
benchmarks/
├── seen/      ← 学習と評価兼用。ルール更新に使用OK
└── unseen/    ← 評価専用。絶対にルール更新に使用禁止
```

### 評価指標

| 指標 | フェーズ2 | フェーズ3以降 |
|---|---|---|
| seen成功率 | 80%以上 | 90%以上 |
| unseen成功率 | — | 80%以上（最重要） |
| 修正コスト | 1〜2回 | 1回 |

> **重要:** フェーズ2ではunseenテスト禁止。過学習のリスクを理解した上で短期突破を優先する。

## ベンチマーク作成方法

### seenタスクの作成

```
benchmarks/seen/ に配置する:
1. 設計書（templates/design_template.md形式）
2. modファイル
3. 期待動作の説明
```

**作成ルール:**
- 1つのmod（アイテム1〜3個）から始める
- copy-from を使用すること
- レシピなしでもOK

### unseenタスクの作成（フェーズ3以降）

**重要な制約:**
- benchmarks/unseen/ に保存する
- ルール更新に使用禁止（外部メディアに保存）
- 人間のみアクセス可能

**タスクタイプ:**

| タイプ | 例 | 難易度 |
|---|---|---|
| 未使用カテゴリ | vehicle, mutation | 高 |
| 複合mod | item + recipe + monster | 高 |
| copy-from禁止 | 新規定義のみ | 中 |
| 大規模 | 10+ アイテム | 高 |

**作成手順:**
1. external/cdda/data/json/ から未使用カテゴリを探す
2. そのカテゴリの既存アイテムを調査
3. 新しいmodを設計（seenの10倍以上の差異）
4. benchmarks/unseen/ に保存

### randomタスク生成

```
benchmarks/random/generator.py

入力:
- アイテムカテゴリ（weapons, food, armor等）
- 数（1〜5）

出力:
- ランダム設計書 + modファイル
```

---

## Level3テスト（意図通り動作）の具体的な手順

### テスト項目

| 項目 | 確認方法 | 異常の基準 |
|---|---|---|
| スポーン確認 | デバッグメニューでアイテムをスポーン | 表示されない |
| レシピ表示 | クラフトメニューで確認 | 表示されない |
| ステータス | アイテムを装備/使用 | クラッシュ |
| バランス | ダメージ/耐久値を比較 | 10倍以上差 |

### 確認手順（CDDA起動後）

```
1. デバッグメニューを開く（`~`キー）
2. "Spawn item" を選択
3. 追加したアイテムIDを入力
4. アイテムが表示されるか確認
5. アイテムを拾って装備
6. ステータス画面で確認

（レシピがある場合）
7. Craftingメニューを開く
8.追加したレシピが表示されるか確認
9. 材料を用意してクラフト
10. 完成品が正しくできるか確認
```

### 異常検出パターン

| 異常 | 検出方法 | 対応 |
|---|---|---|
| スポーンしない | デバッグメニューで表示されない | ID確認、flags確認 |
| クラッシュ | 装備時ゲーム終了 | 必须フィールド不足 |
| バランス崩壊 | 攻撃力が倍以上 | 数値調整 |

### Level3合格基準

```
[ ] アイテムがスポーンする
[ ] アイテムを装備/使用してもクラッシュしない
[ ] レシピがクラフトメニューに表示される
[ ] クラフトしたアイテムが期待通り
[ ] ステータスが範囲内（既存アイテムの±50%以内）
```

---

## rule/capability 判定ルール

### 判定基準

| 原因 | 判定 | 対応 |
|---|---|---|
| 高性能モデルでも同じ失敗 | `rule` | ルールを更新 |
| 高性能モデルは成功 | `capability` | ルール変更禁止、タスク委譲リストに追加 |

### 判定フロー

```
1. 低性能モデルが失敗
2. 高性能モデルで同じタスクを再実装
3. 高性能モデルも失敗 → rule
4. 高性能モデルは成功 → capability
```

> **重要:** これはフェーズ2突破後に実施。フェーズ2では全失敗をruleとして扱う（最短戦略）。

---

## Human Review ポイント

| タイミング | レビュー内容 |
|---|---|
| フェーズ2完了時 | 成功率検証、ルールの妥当性確認 |
| フェーズ3移行時 | unseen成功率確認、ルール肥大化チェック |
| 週次 | logs/summarized/ の集約ログ確認 |

---

## CDDAのJSONサンプル集

> エージェントが参照できるよう、動作確認済みの最小構成を記載する。
> 詳細なフィールド一覧は `external/cdda/doc/JSON/JSON_INFO.md` を参照。

### modinfo.json（完全版）

```json
[
  {
    "type": "MOD_INFO",
    "id": "my_mod",
    "name": "My Mod",
    "authors": [ "Your Name" ],
    "description": "This mod adds custom items.",
    "category": "items",
    "dependencies": [ "dda" ],
    "version": "1.0"
  }
]
```

**category の選択肢:**

| 値 | 用途 |
|---|---|
| `content` | 大量のコンテンツを追加する大規模mod |
| `total_conversion` | ゲームを根本的に変える変換mod |
| `items` | アイテム・レシピの追加 |
| `creatures` | モンスター・NPCの追加 |
| `misc_additions` | その他の雑多な追加 |
| `buildings` | オーバーマップの場所・構造物 |
| `vehicles` | 乗り物・車両パーツ |
| `rebalance` | バランス調整 |
| `magical` | 魔法関連 |
| `item_exclude` | アイテムのスポーン除外 |
| `monster_exclude` | モンスターのスポーン除外 |

---

### アイテム追加（近接武器の例）

```json
[
  {
    "type": "GENERIC",
    "id": "my_mod_iron_rod",
    "name": { "str": "iron rod" },
    "description": "A sturdy iron rod. Good for bashing.",
    "weight": "500 g",
    "volume": "1500 ml",
    "price": "200 USD",
    "material": [ "iron" ],
    "symbol": "/",
    "color": "light_gray",
    "melee_damage": {
      "bash": 12,
      "cut": 0
    },
    "flags": [ "SHEATH_SWORD" ]
  }
]
```

**単位の注意（0.H以降）:**
- 重量: `"500 g"` または `"1 kg"` 形式（旧バージョンは数値のみだった）
- 容量: `"1500 ml"` または `"1 L"` 形式（旧バージョンは数値のみだった）

---

### copy-from の使い方（既存アイテムの継承）

```json
[
  {
    "type": "GENERIC",
    "id": "my_mod_heavy_crowbar",
    "copy-from": "crowbar",
    "name": { "str": "heavy crowbar" },
    "description": "An oversized crowbar, heavier but hits harder.",
    "weight": "2 kg",
    "melee_damage": {
      "bash": 20
    }
  }
]
```

> `copy-from` を使う前に `external/cdda/data/json/` で親アイテムのIDが存在することを確認する。

---

### レシピ追加

```json
[
  {
    "type": "recipe",
    "result": "my_mod_iron_rod",
    "category": "CC_WEAPON",
    "subcategory": "CSC_WEAPON_BASHING",
    "skill_used": "fabrication",
    "difficulty": 2,
    "time": "30 m",
    "autolearn": true,
    "components": [
      [ [ "pipe", 1 ] ]
    ]
  }
]
```

---

### モンスター追加

```json
[
  {
    "type": "MONSTER",
    "id": "my_mod_zombie_armored",
    "copy-from": "mon_zombie",
    "name": { "str": "armored zombie" },
    "description": "A zombie wearing scraps of body armor.",
    "armor_bash": 8,
    "armor_cut": 12,
    "diff": 5
  }
]
```

---

## 設計書テンプレート

> `templates/design_template.md` として保存して毎回使用する

```markdown
## Mod設計書: [mod名]

### 目的
- 何を追加/変更するか

### スコープ
- 含むもの
- 含まないもの（重要）

### ターゲットバージョン
- CDDA: 0.I RC

### 依存関係
- 依存mod: dda（必須）, [その他]

### 参照ファイル（external/cdda/）
- [ ] data/json/[参照ファイル]

### ファイル構成
- modinfo.json
- data/items.json
- data/recipes.json（レシピがある場合）

### 実装順序
1. modinfo.json
2. data/items.json
3. data/recipes.json

### テスト手順
1. CDDAを起動してmodを有効化
2. デバッグメニュー（`~`キー）でアイテムをスポーンして確認
3. クラフトメニューでレシピが表示されることを確認

### 完了条件
- [ ] Level1: JSON構文OK
- [ ] Level2: 起動OK（エラーなし）
- [ ] Level3: 意図通り動作（フェーズ3以降で必須）
```

---

## ルールファイル: CORE.md

> `rules/CORE.md` として保存する。エージェントへの指示の先頭に必ず読ませる。

```markdown
# CDDA Mod開発 コアルール

## 開発の進め方
1. 実装前に必ず設計書（templates/design_template.md）を作成する
2. external/cdda/data/json/ を参照してIDやフラグの正確な綴りを確認する
3. 実装後は必ずJSONの構文チェックを行う（scripts/validate.sh）

## 命名規則
- IDは必ず `mod_prefix_` で始める（例: `mymod_iron_rod`）
- IDに使える文字: 英小文字・数字・アンダースコアのみ
- IDに `#` 文字は使用不可

## 単位（0.H以降）
- 重量: `"500 g"` 形式（旧modが数値のみの場合は変換が必要）
- 容量: `"1500 ml"` 形式（旧modが数値のみの場合は変換が必要）
- 価格: `"200 USD"` 形式

## modinfo.json
- `type`: 必ず `"MOD_INFO"`
- `id`: 必須。他modと重複しない一意のID
- `name`: 必須
- `dependencies`: `[ "dda" ]` を最低限記載する

## copy-from の使い方
- 使用前に external/cdda/data/json/ で親IDの存在を確認する
- abstract アイテムを copy-from する場合、`abstract` フィールドは引き継がれない

## バージョン差分（0.G → 0.H）
- volume/weight の単位が数値から文字列形式に変更
  - 旧: `"volume": 3` → 新: `"volume": "750 ml"`
  - 旧: `"weight": 500` → 新: `"weight": "500 g"`
- その他の差分は version_diff.md を参照

## よくあるエラー
- `unknown type` → typeフィールドのスペルミス
- `copy-from target not found` → 依存modの読み込み順か、IDのスペルミス
- `missing required field` → common_errors.md を参照
- JSON構文エラー → 末尾カンマ、括弧の対応を確認
```

---

## ルールファイル: hints_basic.md

> `rules/hints_basic.md` として保存する。低性能モデル（Qwen / Gemini）への指示時に `CORE.md` と一緒に渡す。

```markdown
# CDDA Mod開発 低性能モデル向け補足ヒント

## このファイルの使い方
CORE.md を読んだ後にこのファイルを読んでください。
迷ったときは external/cdda/data/json/ の既存ファイルをそのままコピーして改変するのが最も安全です。

## modinfo.json を作る手順（ステップバイステップ）
1. テキストエディタで `modinfo.json` を新規作成する
2. 最初の行に `[` を書く
3. 次の行に `{` を書く
4. 以下のフィールドを順番に書く（カンマを忘れずに）:
   - `"type": "MOD_INFO"`
   - `"id": "あなたのmod名（英数字とアンダースコアのみ）"`
   - `"name": "表示名"`
   - `"dependencies": [ "dda" ]`
5. 最後の `}` の後にカンマは不要
6. ファイルの末尾を `]` で閉じる

## よくある間違いと正しい書き方

### 間違い: 末尾カンマ
```json
{
  "type": "MOD_INFO",
  "id": "my_mod",   ← このカンマが最後のフィールドについていてはいけない
}
```

### 正しい書き方
```json
{
  "type": "MOD_INFO",
  "id": "my_mod"   ← 最後のフィールドにカンマなし
}
```

## アイテムのIDを調べる方法
1. `external/cdda/data/json/items/` フォルダを開く
2. 関係しそうなJSONファイルを開く
3. `"id":` で検索して正確なIDをコピーする
4. 自分のJSONの `copy-from` にそのIDを貼り付ける

## 単位の変換早見表
| 旧バージョン（数値） | 0.H以降（文字列） |
|---|---|
| `"weight": 500` | `"weight": "500 g"` |
| `"weight": 1000` | `"weight": "1 kg"` |
| `"volume": 1` | `"volume": "250 ml"` |
| `"volume": 4` | `"volume": "1 L"` |

## 成功判定（最短ルートの合否基準）
| レベル | 基準 | フェーズ2 | フェーズ3 |
|---|---|---|---|
| Level1 | JSON構文OK | 必須 | 必須 |
| Level2 | 起動OK | 必須 | 必須 |
| Level3 | 意図通り動作 | 不要 | 必須 |

### 条件付き合格（フェーズ2のみ）
- 1〜2回の軽微修正でLevel2に達すれば合格とする
- 修正コスト ≤ 2 = 合格
```

---

## ルールファイル: hints_advanced.md

> `rules/hints_advanced.md` として保存する。高性能モデル（Kilo Code / OpenCode）への指示時に `CORE.md` と一緒に渡す。

```markdown
# CDDA Mod開発 高性能モデル向け補足ヒント

## 設計判断の基準

### copy-from vs 新規定義
- 既存アイテムと80%以上共通する場合は `copy-from` を使う
- 全く異なる動作が必要な場合は新規定義する
- `abstract` アイテムを copy-from するとゲームにスポーンしないため注意

### ID設計
- mod間の衝突を避けるため、プレフィックスはプロジェクト固有の短縮形にする
  - 例: プロジェクト名が "SurvivalPlus" なら `sp_` をプレフィックスに使う
- 将来の拡張を考えてカテゴリを名前に含める
  - 例: `sp_weapon_iron_rod`, `sp_food_dried_meat`

### ファイル分割の判断
- 同じ `type` のオブジェクトは同じファイルにまとめる
- 1ファイル100オブジェクト以上になったら分割を検討する
- 相互依存するオブジェクト（アイテムとそのレシピ）は同じディレクトリに置く

## トレードオフの整理

### バランス調整
- `copy-from` でステータスだけ変えるとき、元の値を必ずコメントに残す
- 数値変更は一度に1〜2フィールドにとどめ、影響範囲を確認してから次に進む

## ルール更新の判断基準
- 低性能モデルの `capability` 起因の失敗を見て「この失敗が高性能モデルでも起きうるか」を判断する
- 起きうるなら `CORE.md` に追加、起きないなら `hints_basic.md` に追加する
```

---

## ルールファイル: version_diff.md

> `rules/version_diff.md` として保存する。旧modの移植時に必ず参照する。

```markdown
# CDDAバージョン差分メモ

## 0.G → 0.H の主な変更

### 単位の文字列化（破壊的変更）
- `volume` と `weight` が数値から文字列形式に変更
  - 旧: `"volume": 3`, `"weight": 500`
  - 新: `"volume": "750 ml"`, `"weight": "500 g"`
- 旧modを移植するときは全ての volume / weight フィールドを変換する

### その他（調査中・随時更新）
- 確認した差分はここに追記する

## 0.H → 0.I の主な変更

### （調査中）
- `external/cdda/doc/` の changelog やリリースノートを確認して随時追記する
- 変更確認コマンド:
  ```bash
  grep -r "TODO\|CHANGED\|DEPRECATED" external/cdda/doc/ | head -30
  ```

## バージョン確認方法
- `external/cdda/data/version.json` または `external/cdda/VERSION` を確認する
```

---

## ルールファイル: common_errors.md

> `rules/common_errors.md` として保存する。エラーが発生するたびに追記する。

```markdown
# よくあるエラーと解決策

## エラー一覧

### `unknown type: XXX`
- **原因:** `type` フィールドの値のスペルミス
- **種別:** rule
- **解決策:** `external/cdda/data/json/` で正しい type 名を検索して確認する
- **例:** `"type": "GENRIC"` → `"type": "GENERIC"`

### `can't find copy_from target 'XXX'`
- **原因:** `copy-from` で指定したIDが存在しない
- **種別:** rule
- **解決策:**
  1. `external/cdda/data/json/` でIDを grep して存在確認する
  2. 依存modが `dependencies` に記載されているか確認する
  3. IDのスペルミスを確認する

### `JSON parse error` / `unexpected token`
- **原因:** JSONの構文エラー
- **種別:** rule
- **解決策:** `scripts/validate.sh` を実行してエラー行を確認する。末尾カンマ、括弧の対応を確認する

### `missing required field: XXX`
- **原因:** 必須フィールドが欠けている
- **種別:** rule
- **解決策:** `external/cdda/doc/JSON/JSON_INFO.md` で該当 type の必須フィールドを確認する

### volume/weight の値が不正
- **原因:** 旧バージョン形式（数値）のまま移植した
- **種別:** rule
- **解決策:** `version_diff.md` の単位変換表を参照して文字列形式に変換する

---
※ 新しいエラーが発生したらこのファイルに追記する
```

---

## エージェントレポートテンプレート

> `logs/agent_reports/YYYY-MM-DD_[mod名]_評価レポート.md` として保存する。

```markdown
# ルール評価レポート

- 日時: YYYY-MM-DD
- 対象mod:
- 評価モデル: Qwen Code / Gemini CLI
- 使用ルール: CORE.md + hints_basic.md

## 試行結果サマリー

| 試行 | 結果 | 原因種別 | 修正コスト | 備考 |
|---|---|---|---|---|
| 1 | 合格/条件付き/不合格 | rule/capability | 0/1/2 | |
| 2 | | | | |
| 3 | | | | |
| ... | | | | |

## 集計

- 総試行回数:
- 合格:
- 条件付き合格:
- 不合格:
- **成功率（合格+条件付き）:** xx% （目標: 80%以上）

## 修正コスト分布
- 修正0回:
- 修正1回:
- 修正2回:

## 失敗パターン TOP3
（common_errors.md に反映済みのものはチェック）
- [ ] 失敗パターン1 → 反映先:
- [ ] 失敗パターン2 → 反映先:

## 次回試行に向けた改善点
```

---

## scripts/validate.sh

> CDDAはゲーム起動時にJSONをパースするため、事前に構文チェックするスクリプト。

```bash
#!/bin/bash
# validate.sh — mod内の全JSONファイルの構文チェック

MOD_DIR="${1:-.}"
ERRORS=0

echo "=== JSON Validation: $MOD_DIR ==="

# NOTE: パイプ経由の while read はサブシェルで実行されるため ERRORS が
# 親シェルに伝播しない。プロセス置換 < <(...) を使って同一シェルで実行する。
while read -r file; do
  if python3 -m json.tool "$file" > /dev/null 2>&1; then
    echo "  OK: $file"
  else
    echo "  NG: $file"
    python3 -m json.tool "$file" 2>&1 | head -5
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$MOD_DIR" -name "*.json")

if [ "$ERRORS" -eq 0 ]; then
  echo "=== All files passed ==="
else
  echo "=== $ERRORS file(s) failed ==="
  exit 1
fi
```

**使い方:**
```bash
chmod +x scripts/validate.sh

# 特定のmodを検証
bash scripts/validate.sh mods/small/my_mod/

# プロジェクト全体を検証
bash scripts/validate.sh mods/
```

---

## 低性能モデルへの初期プロンプト（最短ルート用）

### Qwen Code 向け（評価・成功率計測用）

```
あなたはCataclysm: Dark Days Ahead (CDDA) 0.I RC のmod開発者です。
以下のルールファイルを読み、その内容に従ってmodを実装してください。

## 読むべきルールファイル（必ず最初に読むこと）
1. rules/CORE.md
2. rules/hints_basic.md

## 参照してよいファイル
- external/cdda/data/json/（IDやフィールドの確認のみ）

## 実装するmod
[設計書の内容をここに貼り付ける]

## 合否基準（非常重要）
- Level1: JSON構文OK → 必須
- Level2: 起動OK（エラーなし）→ 必須
- Level3: 意図通り動作 → フェーズ2では不要

## 条件付き合格
- 軽微な修正（1〜2回）でLevel2に達すれば合格とする
- 焦らず、確実に実装すること
```

---

## 最短突破ロードマップ（3〜5日）

### Day 1: 環境整備
1. `external/cdda/` にCDDA 0.I RC を配置
2. `.gitignore` 作成
3. `scripts/validate.sh` 配置
4. `rules/CORE.md` 作成（最小限）

### Day 2: 超単純mod実装
1. 設計書作成（アイテム1個、copy-fromあり）
2. Kilo Codeで実装
3. テストして動作確認
4. `common_errors.md` にエラー記録

### Day 3-5: ルール評価サイクル
1. Qwenに同じmodを30回実装させる（分割して実施）
2. 成功率記録（5回ごとに中間集計）
3. 頻出エラーTOP3を特定
4. `hints_basic.md` を更新

### Day 6: フェーズ2突破確認
1. 30回中24回（80%）成功達成確認
2. 条件付き合格OK
3. フェーズ2完了

---

## コスト最適化エンジン（長期戦略）

### 基本原則

```
if タスク難易度 < threshold:
    Qwen
else:
    Kilo Code
```

### 難易度推定基準

| 基準 | 低難易度 | 高難易度 |
|---|---|---|
| JSON行数 | 1〜50 | 100+ |
| type数 | 1 | 5+ |
| copy-from | 浅 | 深 |
| 新規概念 | なし | あり |

### 判断ロジック

1. **JSON行数 < 50**: QwenでOK
2. **type数が1つ**: QwenでOK
3. **新規概念なし**: QwenでOK
4. **どれかに該当**: Kilo Codeへ委譲

---

## ログ集約システム（フェーズ3以降）

### 構造

```
logs/
├── errors/        ← 生ログ（詳細）
└── summarized/   ← 集約ログ（AI生成）
```

### 集約の頻度

- 毎日1回、AIがエラーを分類
- 週次でTOP5を `common_errors.md` に反映

### 集約プロンプト

```
logs/errors/ の最新ログ10件を分析してください:
1. エラーを分類
2. 頻出パターンを抽出
3. common_errors.md 更新案を提示
```

---

## 最初のアクションプラン

### 環境構築（Day 1）
1. `external/cdda/` にCDDA 0.I RC のファイルを配置する
2. `.gitignore` に `external/cdda/` を追記する
3. `scripts/validate.sh` を配置して `bash scripts/validate.sh external/cdda/data/mods/` で動作確認する

### ルールファイルの初期作成（Day 1）
4. `rules/CORE.md` を本ドキュメントの雛形から作成する
5. `rules/hints_basic.md` を本ドキュメントの雛形から作成する
6. `rules/common_errors.md` を本ドキュメントの雛形から作成する

### フェーズ1: 小規模mod開発（Day 2）
7. `templates/design_template.md` を使って設計書を書く
8. Kilo Code（高性能）で実装し、`scripts/validate.sh` で検証する
9. 発生したエラーをすべて `logs/errors/` にログ化し `rules/common_errors.md` に反映する

### フェーズ2: ルール評価サイクル（Day 3-6）
10. Qwen に `CORE.md` + `hints_basic.md` を渡して同じmodを30回実装させる（5回ごとに中間集計）
11. 結果を `logs/agent_reports/` にレポートとしてまとめる
12. 頻出エラーTOP3を `hints_basic.md` に追加する
13. 成功率80%以上になったらフェーズ3へ進む

### フェーズ3: 長期戦略へ（週次以降）
14. unseenタスクベンチマークの導入
15. ルール構造化（JSON化）
16. human reviewポイントの整備
17. コスト最適化エンジンの実装

---

## 重要な詰みポイント回避

| No | 詰みポイント | 回避策 |
|---|---|---|
| ① | rule/capability判定崩壊 | フェーズ2では全失敗をruleとして扱う |
| ② | ルール爆発 | 頻出TOP3だけ対応、抽象化して統合 |
| ③ | 偽の成功率 | フェーズ3でunseenテスト導入 |
| ④ | 壊れたmod量産 | Level3テスト導入（フェーズ3） |
| ⑤ | ログ崩壊 | 集約システム導入 |
| ⑥ | モデル進化 | モデル非依存のルール設計 |
| ⑦ | 初期コスト地獄 | 最短突破ルートで3〜5日実現 |

---

## 計画書の更新履歴

| 日付 | 更新内容 |
|---|---|
| 2026-04-15 | 初版作成。issue.mdの問題点を反映してベンチマーク構造、テストレベル、rule/capability判定ルールを追加 |
| 2026-04-15 | ベンチマーク作成方法(Level3テスト手順)、rule/capability判定タイミングを追加 |
| 2026-04-15 | **バグ修正・信頼性改善:** (1) validate.sh のサブシェルバグを修正（`find \| while` → プロセス置換）。(2) フェーズ2の評価回数を n=10 → n=30 に変更（統計的信頼性確保、完了条件 24/30以上）。(3) Level3テストに自動化方針（Step A/B/C）を追記。 |