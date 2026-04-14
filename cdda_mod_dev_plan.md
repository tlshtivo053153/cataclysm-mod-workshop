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

---

## フェーズ構成

### フェーズ1 — 小規模mod / 旧mod移植（ルール構築期）

**完了条件:** 以下をすべて満たすこと
- [ ] 小規模mod（アイテム追加など）を1本、エラーなしで動作させる
- [ ] 旧modを1本、0.I RCで動作するよう移植する
- [ ] 発生したエラーをすべてログ化し `common_errors.md` に反映する
- [ ] `CORE.md` に10件以上のルールが記載されている

**作成順序（難易度順）:**
1. 旧modの移植 — バージョン差分の学習に最適。エラーメッセージがそのままルールになる
2. 単純アイテム追加mod — 武器・食料1〜3種類。JSON構造の基礎習得
3. 簡単なレシピ追加 — 既存アイテムのクラフトレシピ追加

### フェーズ2 — ルール評価サイクル

**完了条件:** 以下をすべて満たすこと
- [ ] Qwen がルールファイル（`CORE.md` + `hints_basic.md`）のみを参照して、フェーズ1と同じmodを**エラーなしで**再実装できる
- [ ] `rule` 起因の成功率が **80%以上**（Qwen で10回試行中8回以上合格）
- [ ] `capability` 起因の失敗は高性能モデルへの委譲タスクとして `logs/agent_reports/` に記録されている
- [ ] 全失敗パターンの原因種別が `common_errors.md` に記載されている

**`capability` 起因失敗の扱い:**
- ルールは変更しない
- `logs/agent_reports/` に「このタスクは低性能モデルの能力限界」と記録する
- 高性能モデルへ委譲するタスクリストに追加する
- 成功率の計算から除外せず、「委譲必要タスク」として別集計する

**サイクルの回し方:**
1. Qwen に `CORE.md` + `hints_basic.md` を渡して同じmodを再実装させる
2. 成功・失敗と原因種別（`rule` / `capability`）をログに記録する
3. `rule` 起因の失敗は `hints_basic.md` を更新して再試行する
4. `capability` 起因の失敗は委譲リストに追加してスキップする
5. `rule` 起因の成功率が80%以上になるまで繰り返す

### フェーズ3 — 中・大規模mod

**フェーズ移行条件:** フェーズ2の完了条件を満たしていること

- 中規模mod: 新アイテム・職業・派閥など
- 大規模mod: シナリオ・世界観の追加
- ルール強化: スキーマ定義・自動テスト整備

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
│   ├── small/              ← フェーズ1: 小規模mod
│   ├── medium/             ← フェーズ3: 中規模mod
│   └── large/              ← フェーズ3: 大規模mod
├── logs/
│   ├── errors/             ← エラーログ（YYYY-MM-DD_mod名_エージェント名.md）
│   └── agent_reports/      ← ルール評価レポート
├── templates/
│   ├── modinfo.json        ← modinfo.jsonのテンプレート
│   └── design_template.md ← 設計書テンプレート
├── scripts/
│   └── validate.sh         ← JSONバリデーションスクリプト
└── .gitignore
```

### .gitignore

```
external/cdda/
logs/
*.swp
```

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
- [ ] エラーなしで起動する
- [ ] アイテムが正しくスポーンする
- [ ] レシピが機能する
```

---

## ルールファイル: CORE.md（雛形）

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

## エージェント運用ルール

### 低性能モデルによるルール評価の既知の問題と対策

#### 問題1: 失敗原因の切り分けが難しい

失敗したとき「ルールの説明が不十分」なのか「モデルの能力の限界」なのかが判別できない。
能力起因の失敗をルールで補おうとすると、ルールが際限なく膨れ上がる。

**対策:** ログの「原因種別」欄に必ず以下のどちらかを記録する。
- `rule`: ルールに記載がなかった・説明が不足していた → `CORE.md` または `hints_basic.md` を更新する
- `capability`: ルールは正しいがモデルが従えなかった → ルールは変更せず、タスクを高性能モデルに委譲する判断材料にする

#### 問題2: 特定モデルへの過剰最適化

Qwen / Gemini に合わせてルールを書き続けると、それらのモデルでしか機能しない冗長なルールができあがり、高性能モデルでの利用時に邪魔になる。

**対策:** ルールをレベルで分離する。

| ファイル | 対象 | 内容 |
|---|---|---|
| `rules/CORE.md` | 全モデル共通 | 高性能モデルでも有効な最小限のルール |
| `rules/hints_basic.md` | 低性能モデル向け | 冗長な説明・具体例・ステップバイステップの手順 |
| `rules/hints_advanced.md` | 高性能モデル向け | 設計判断・トレードオフ・応用パターン |

低性能モデルへの指示: `CORE.md` + `hints_basic.md` を渡す
高性能モデルへの指示: `CORE.md` + `hints_advanced.md` を渡す

#### 問題3: RPD制限による評価サンプル不足

Gemini は200〜300 RPD という制限があり、1日に試行できる回数が少ない。

**対策:** 役割を分担する。

| モデル | 役割 |
|---|---|
| Qwen Code（1000 RPD） | メイン評価エンジン。成功率計測の試行を担う |
| Gemini CLI（200〜300 RPD） | 別観点の検証。異なるプロンプト構成・別タスクの検証に使う |

---

### 高性能モデル（Kilo Code / OpenCode）のタスク
- 初回mod設計と実装
- `external/cdda/` を調査して `version_diff.md` を更新する
- 難しいバグの原因特定とルールへの反映
- 低性能モデルが `capability` 起因で失敗したタスクの代替実装

### 低性能モデルのタスク分担

| モデル | タスク |
|---|---|
| Qwen Code | ルール評価（成功率計測）・バリエーション生成・JSONバリデーション |
| Gemini CLI | 別プロンプト構成での検証・Qwenと異なる観点からのルール評価 |

### ルール評価の合否基準

| 評価 | 基準 |
|---|---|
| 合格 | エラーなしで起動 + 追加コンテンツが動作する |
| 条件付き合格 | 軽微な修正（1〜2箇所）で動作する |
| 不合格 | 起動エラー、またはコンテンツが動作しない |

**目標成功率:** 80%以上（Qwen で10回試行中8回以上合格）

### Kilo Codeへの初期システムプロンプト（雛形）

```
あなたはCataclysm: Dark Days Ahead (CDDA) 0.I RC のmod開発者です。

## 参照先
- ゲームのJSONファイル: external/cdda/data/json/
- 公式modガイド: external/cdda/doc/MODDING.md
- JSONリファレンス: external/cdda/doc/JSON/JSON_INFO.md
- 開発ルール: rules/CORE.md
- バージョン差分: rules/version_diff.md
- エラー一覧: rules/common_errors.md

## 必ず守ること
1. 実装前に設計書を作成する
2. external/cdda/ を参照してIDやフラグの正確な綴りを確認する
3. 実装後は scripts/validate.sh でJSONを検証する
4. 問題が発生したら logs/errors/ にログを残す
```

### ログの残し方

ファイル名: `logs/errors/YYYY-MM-DD_[mod名]_[エージェント名].md`

```markdown
# エラーログ

- 日時: YYYY-MM-DD
- mod名:
- エージェント:
- CDDAバージョン: 0.I RC

## 発生したエラー
（エラーメッセージをそのまま貼り付ける）

## 原因種別
- [ ] `rule` — ルールに記載がなかった・説明が不足していた
- [ ] `capability` — ルールは正しいがモデルが従えなかった

## 原因

## 解決策

## ルールへの反映内容
（`rule` の場合のみ: rules/ のどのファイルに何を追記したか）
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

find "$MOD_DIR" -name "*.json" | while read -r file; do
  if python3 -m json.tool "$file" > /dev/null 2>&1; then
    echo "  OK: $file"
  else
    echo "  NG: $file"
    python3 -m json.tool "$file" 2>&1 | head -5
    ERRORS=$((ERRORS + 1))
  fi
done

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

## ルールファイル: hints_basic.md（雛形）

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
```

---

## ルールファイル: hints_advanced.md（雛形）

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
- 低性能モデルの `capability` 起因の失敗を見て「同じ失敗が高性能モデルでも起きうるか」を判断する
- 起きうるなら `CORE.md` に追加、起きないなら `hints_basic.md` に追加する
```

---

## ルールファイル: version_diff.md（雛形）

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

## ルールファイル: common_errors.md（雛形）

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

| 試行 | 結果 | 原因種別 | 備考 |
|---|---|---|---|
| 1 | 合格 / 条件付き / 不合格 | rule / capability / — | |
| 2 | | | |
| 3 | | | |
| ... | | | |

## 集計

- 総試行回数:
- 合格:
- 条件付き合格:
- 不合格（rule起因）:
- 不合格（capability起因）:
- **rule起因 成功率:** xx% （目標: 80%以上）

## rule起因の失敗パターン
（common_errors.md または hints_basic.md に反映済みのものはチェック）
- [ ] 失敗パターン1 → 反映先:
- [ ] 失敗パターン2 → 反映先:

## capability起因の失敗タスク（高性能モデル委譲リスト）
- タスク名: 理由:

## 次回試行に向けた改善点
```

---

## 低性能モデルへの初期プロンプト（雛形）

### Qwen Code 向け（評価・成功率計測用）

```
あなたはCataclysm: Dark Days Ahead (CDDA) 0.I RC のmod開発者です。
以下のルールファイルを読み、その内容に従ってmodを実装してください。

## 読むべきルールファイル（必ず最初に読むこと）
1. rules/CORE.md
2. rules/hints_basic.md
3. rules/common_errors.md

## 参照してよいファイル
- external/cdda/data/json/（IDやフィールドの確認のみ）

## 実装するmod
[設計書の内容をここに貼り付ける]

## 禁止事項
- ルールファイルに記載のない方法を使わない
- external/cdda/ 以外の外部情報を参照しない
- 実装後は必ず scripts/validate.sh で検証すること
```

### Gemini CLI 向け（別観点の検証用）

```
あなたはCataclysm: Dark Days Ahead (CDDA) 0.I RC のmod開発者です。
以下のルールファイルを読み、その内容に従ってmodを実装してください。

## 読むべきルールファイル（必ず最初に読むこと）
1. rules/CORE.md
2. rules/hints_basic.md

## 検証の観点
Qwenとは異なるアプローチで実装を試みてください。
具体的には:
- フィールドの順序を変えて記述する
- copy-from を使わずに全フィールドを明示して書く（比較用）

## 実装するmod
[設計書の内容をここに貼り付ける]
```

---

## 最初のアクションプラン

### 環境構築
1. `external/cdda/` にCDDA 0.I RC のファイルを配置する
2. `.gitignore` に `external/cdda/` を追記する
3. `scripts/validate.sh` を配置して `bash scripts/validate.sh external/cdda/data/mods/` で動作確認する

### ルールファイルの初期作成
4. `rules/CORE.md` を本ドキュメントの雛形から作成する
5. `rules/hints_basic.md` を本ドキュメントの雛形から作成する
6. `rules/hints_advanced.md` を本ドキュメントの雛形から作成する
7. `rules/common_errors.md` を本ドキュメントの雛形から作成する
8. `external/cdda/doc/` の changelog を読んで `rules/version_diff.md` の 0.H→0.I 差分を埋める

### フェーズ1: 小規模mod開発
9. `templates/design_template.md` を使って設計書を書く
10. Kilo Code（高性能）で実装し、`scripts/validate.sh` で検証する
11. 発生したエラーをすべて `logs/errors/` にログ化し `rules/common_errors.md` に反映する

### フェーズ2: ルール評価サイクル
12. Qwen に `CORE.md` + `hints_basic.md` を渡して同じmodを10回再実装させる
13. 結果を `logs/agent_reports/` にレポートとしてまとめる
14. `rule` 起因の失敗は `hints_basic.md` を更新して再試行する
15. `rule` 起因の成功率が80%以上になったらフェーズ3へ進む
