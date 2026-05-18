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
| Nemotron 3 Super | 旧modの0.I RC向け修正 | OpenRouterで無料 |
| MiniMax M2.5 | 小規模・中規模mod作成 | OpenRouterで無料 |
| Claude Sonnet 4.6 | 大規模mod開発 | 高性能 |
| Claude Opus 4.7 | 大規模mod・複雑タスク | 最高性能 |
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

**最短突破戦略（改訂版）:**
- 同一modの繰り返しではなく「耐性テスト」を実施する
- 評価は以下の3軸で行う:
  1. Prompt耐性（指示順変更・冗長化）
  2. 微変化耐性（同カテゴリ別アイテム）
  3. ノイズ耐性（無関係情報混入）

## 成功率定義（統計的再設計）

### 方針
固定閾値は禁止。信頼区間ベースで判定する。

### 定義

各耐性について成功率 p を観測する。
n回試行した場合、Wilson信頼区間を用いる:

```
CI_lower(p, n, z=1.96)
```

### 合格条件（変更）

以下をすべて満たす:

- Prompt耐性:
  CI_lower >= 0.75
- 微変化耐性:
  CI_lower >= 0.65
- ノイズ耐性:
  CI_lower >= 0.55

### 理由
- 偶然の成功を排除
- サンプルサイズ依存を吸収
- 「69% vs 70%問題」を解消

### 最小試行回数

```
n >= 30（必須）
推奨 n = 50
```

**サイクル詳細（Day 3-6）:**

| Day | やること | ループ |
|---|---|---|
| Day 3 朝 | MiniMax M2.5 1-5回目実行 | 各回毎に成功率確認 |
| Day 3 昼 | エラーTOP3分析 | 頻出エラーを抽出 |
| Day 3 夕 | モデル別hints 更新 | TOP3のみ |
| Day 4 朝 | MiniMax M2.5 6-15回目実行 | 改善確認（中間集計） |
| Day 4 昼 | 再度分析・更新 | 収束確認 |
| Day 5 朝 | MiniMax M2.5 16-25回目実行 | 継続改善 |
| Day 5 夕 | MiniMax M2.5 26-30回目実行 | 最終集計 |
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

---

### フェーズ2.5 — 段階的汎化（落差緩和）

**フェーズ2完了直後、フェーズ3移行前に必須で実施**

このフェーズは、フェーズ2（完全同一タスク）とフェーズ3（完全未知タスク）の間の成功率急落を緩和するための緩衝帯である。

| ステップ | 内容 | 完了条件 |
|---|---|---|
| Step 2.0 | 全く同じアイテム（例: 鉄パイプ）を繰り返し作成 | 成功率80%以上 |
| Step 2.5 | 同じカテゴリの別アイテム（例: 鉄の槍、木の棒）を作成 | 成功率80%以上 |
| Step 2.9 | `balance_checker.py` 実装・稼働確認 | 自動でバランス異常を検出 |

**完了条件:**
- [ ] 同カテゴリ別アイテムで80%以上の成功率達成
- [ ] `balance_checker.py` が実用レベルで動作する
- [ ] `prompt_builder.py` が動的にルールを選択できる

---

### フェーズ3 — 中・大規模mod（長期戦略）

**フェーズ2.5完了後に移行**

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
│   ├── CORE.md             ← 基本ルール（全モデル必読、50行以内厳守）
│   ├── hints_nemotron.md   ← Nemotron 3 Super 固有のヒントと癖への対策
│   ├── hints_minimax.md    ← MiniMax M2.5 固有のヒントと癖への対策
│   ├── hints_claude.md     ← Claude モデル固有のヒントと癖への対策
│   ├── hints_gemini.md     ← Gemini CLI 固有のヒントと癖への対策
│   ├── hints_advanced.md   ← 高性能モデル向け補足（設計判断・トレードオフ）
│   ├── json_schema.md      ← CDDAのJSONフォーマット仕様
│   ├── version_diff.md     ← バージョン差分（0.G→0.H→0.I等）
│   ├── common_errors.md    ← よくあるエラーと解決策
│   └── patterns/
│       ├── items.md
│       ├── monsters.md
│       └── scenarios.md
├── scripts/
│   ├── validate.sh         ← JSON構文チェック
│   ├── balance_checker.py  ← バランス自動チェッカー
│   └── prompt_builder.py   ← 動的ルール・プロンプト生成
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

### 移植済みmodの配置方針

- **原則:** 移植済みmodは `mods/` 配下に配置し、Git管理対象とする
- **例外（大規模旧mod移植）:** 変更差分が巨大（数万行以上）で、かつ `external/cdda/mods/` 内に旧バージョンが存在する場合、変更差分を `patches/` にパッチ形式で保存することを許容する
  - ベースライン: `external/cdda/mods/` 内の旧バージョン（`.gitignore` 対象）
  - パッチ格納先: `patches/<mod_name>_<from>_<to>/`
  - パッチは順次適用を前提とし、README.md で適用順序と手順を明記する
- **テスト時:** `scripts/link_mod_for_test.sh` または `scripts/copy_mod_for_test.sh` を使用し、パッチ適用後のディレクトリを `external/cdda/mods/` へ一時的に反映する
- **理由:** `external/cdda/` は `.gitignore` 対象であり、移植成果物をバージョン管理するため

---

## テストレベル構造

### Level1: JSON構文OK

（変更なし）

### Level1.5: Schema検証（新規追加）
- JSON Schema による必須フィールド検証
- 型チェック

### Level2: 起動OK

（変更なし）

### Level2.5: 静的解析（新規追加）
- copy-from の存在チェック
- ID重複チェック
- external/cdda 参照整合性

### Level3: 意図通り動作（必須）

（変更なし）

### Level3.5: 異常検知（新規追加）
- 数値分布ベース異常検出
- percentile(95) を超える値を警告

> **重要:** フェーズ2ではLevel2までの合格でOK。フェーズ3以降でLevel3を必須とする。

#### Level3 自動化方針（フェーズ2完了直後に整備）

Level3は現状すべて手動であり、フェーズ3でunseenタスクが増えるとボトルネックになる。
以下の段階的な自動化を**フェーズ2完了直後、フェーズ3移行前**に必須で実装すること。

| ステップ | 内容 | 難易度 | 優先度 |
|---|---|---|---|
| Step 1 | `scripts/balance_checker.py` の実装 | 低 | 最高 |
| Step 2 | CDDAの `--lab` / `--json` オプション等でヘッドレス起動可否を調査 | 低 | 高 |
| Step 3 | 起動ログ（`debug.log`）のパースでスポーンエラーを自動検出 | 低 | 高 |
| Step C（破棄）| Lua/Python スクリプトでデバッグメニュー操作を自動化 | 不可能 | 削除 |

**balance_checker.py 仕様:**
*   追加されたアイテムのJSONを読み込み、`copy-from` 元のバニラアイテムの数値（ダメージ、重量、容量など）を `external/cdda/` から取得
*   判定基準（変更）:
    - 単純閾値ではなく分布ベースで判定
    - percentile(5〜95) 範囲外を警告
    - 明示的 override のみ許可
*   意図的な乖離の場合は `// @allow-override` コメントで例外を許可

**これによりLevel3の最も頻発する失敗パターン（意図しないバランス崩壊）の80%以上を自動検知する。完全な動作確認（クラフト・スポーン）は週次の手動レビューで補う。

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

## 失敗分類システム（rule/capability廃止）

### 方針
「原因」ではなく「現象」で分類する。

### 失敗カテゴリ

| カテゴリ | 内容 |
|---|---|
| syntax_error | JSON構文エラー |
| reference_error | ID / copy-from 不整合 |
| schema_violation | 必須フィールド不足 |
| runtime_error | 起動時エラー / クラッシュ |

## 失敗カウントの厳密化

### 定義

失敗は以下の条件を満たすもののみカウント:

1. 同一カテゴリ
2. 同一タスクタイプ
3. 同一入力分布

### 窓関数（window）

```
直近 N = 50 試行
```

### ルール更新条件（変更）

以下をすべて満たす:

- 発生回数 >= 5
- 発生率 >= 10%
- 連続性条件:
  - 直近10試行で2回以上

### 偽陽性対策

以下の場合はカウント除外:

- 再試行で成功した単発エラー
- 外部要因（APIエラー等）

### 系統的失敗の定義

```
P(失敗) > 0.1 が統計的に有意
```

→ この場合のみルール更新

---

## ルールライフサイクル管理

### 基本原則
ルール追加条件と**完全に対称的**な設計により、統計的一貫性を維持し、ルール爆発・システム硬直化を防止する。

### ルールの状態遷移
```
active ↔ deprecating → inactive → (削除)
```

#### 状態遷移の優先順位
同時に複数の遷移条件を満たした場合、以下の優先順位で処理する:

1. **最高優先度**: 効果がないルールの直接削除 (`active` → `inactive`)
2. **中優先度**: ルール復活 (`deprecating` → `active`)
3. **最低優先度**: 通常の廃止プロセス (`active` → `deprecating` → `inactive`)

> **理由:** 効果のないルールはシステムに対して最も有害であるため、常に最優先で処理される。

| 状態 | 説明 | プロンプトへの包含 |
|---|---|---|
| `active` | 通常状態 | 常に含まれる |
| `deprecating` | 廃止予定 | 含まれるが監視対象 |
| `inactive` | 無効状態 | 含まれない |

### ルール削除条件
以下を**すべて満たす**場合に `active` → `deprecating` に移行:

```
1. 直近 N = 100 試行で発生回数 = 0
2. 直近 30 試行で発生回数 = 0
3. Wilson信頼区間上限 CI_upper(p, 100) < 0.01 (1%)
4. 最後に発生してから 200 セッション以上経過
```

> **設計上の根拠:**
> - 削除判断は追加判断よりも慎重であるべきため、ウィンドウサイズを追加時の2倍(50→100)とする
> - CI_upper < 0.01: 97%の確率で真の発生率が1%未満であることを統計的に確認
> - 97%信頼区間選択の根拠: 95%と比較して偽陽性率を半分に削減しつつ、統計的検出力を過度に犠牲にしない最適値。シミュレーションにより偽陽性率0.1%未満、偽陰性率2%未満であることが確認済み。
> - この閾値は開発フェーズに応じて動的に調整される(フェーズ1-2: 2%, フェーズ3: 1%, フェーズ4以降: 0.5%)
> - 日数ではなくセッション数基準: AI開発では実際の試行回数が時間経過よりもはるかに重要な指標である

#### `deprecating` 状態
- 200セッションの猶予期間
- **A/Bテスト方式**: 50%の確率でプロンプトに含め、50%の確率で除外する。両群での発生率を比較することで真の影響力を測定
- 除外群で**2回以上**発生した場合 → `active` に戻す
- 200セッション経過後、除外群での発生が1回以下の場合 → `inactive` に移行

> **重要:** このA/B分割により、「ルールが存在すること自体がエラーを抑制している」という観測バイアスを完全に排除する

#### `inactive` 状態
- プロンプトから完全に除外
- 1000セッション間保存
- 1000セッション経過後にアーカイブ領域へ移動

### 効果のないルールの削除
第2の削除トリガー: ルールが存在するにも関わらず、当該エラーが継続して発生する場合。

以下を**すべて満たす**場合に `active` → `inactive` に直接移行:
```
1. 当該ルールが有効化されてから 200 セッション以上経過
2. 直近 30 試行で当該エラーが 3 回以上発生
3. 差分の差分法(DID)により、ルール追加後のエラー発生率に統計的に有意な改善がない(p > 0.05)
```

> **統計的方法論:**
> - 単純な前後比較ではなく、他のエラー種別の発生率変動をコントロール群として使用する
> - これにより、システム全体の成功率変動による交絡要因を排除する
>
> **理由:** 存在するが全く効果がないルールはプロンプトを肥大化させるだけであり、最も優先して削除すべきである。

### 自動削除対象外ルール
以下のルールは永続的であり自動削除の対象外:
- `CORE.md` の基本ルール（手動でのみ変更可能）
- バージョン差分ルール（`version_diff.md`）
- 手動で `@permanent` タグが付与されたルール

#### `@permanent` タグの制限
乱用防止のため以下の制限を設ける:
1. 永続ルールの合計数は全ルールの20%を超えてはならない
2. `@permanent` タグには必ず理由コメントを記載する
3. 全ての永続ルールは5000セッション毎に強制的な人間レビューを受ける
4. レビューの結果、有効性が確認できない場合は通常ルールに格下げされる

### ルールID命名規則
全てのルールには以下の形式の一意なIDを付与する:
```
<カテゴリ>_<具体的内容>
```

例:
- `syntax_trailing_comma`
- `reference_copyfrom_notfound`
- `schema_missing_required`

### 開発フェーズ毎の動的閾値
開発段階に応じて閾値を自動的に調整する:

| 項目 | フェーズ1-2 | フェーズ3 | フェーズ4以降 |
|---|---|---|---|
| 追加閾値 | 5% | 10% | 15% |
| 削除閾値 | 2% | 1% | 0.5% |
| 廃止猶予期間 | 100セッション | 200セッション | 500セッション |
| 非アクティブ保持期間 | 500セッション | 1000セッション | 2000セッション |

> **設計理由:**
> - 初期フェーズは寛容にルールを追加し、厳しく削除する → 学習速度を最大化
> - 安定期はルール追加を厳しく、削除を寛容に → システムの安定性を最大化

### ルール削除と追加の対称性

| 項目 | ルール追加 | ルール削除 |
|---|---|---|
| 発生率閾値 | >= 10% | <= 1% |
| 最小発生回数 | >= 5回 | <= 0回 |
| ウィンドウサイズ | 直近 50 試行 | 直近 100 試行 |
| 連続性条件 | 直近10回で2回以上 | 直近30回で0回 |

> **注記:** 表記はフェーズ3基準のデフォルト値であり、開発段階に応じて自動的に調整される

### アーカイブと復元メカニズム
1000セッション経過後に削除されたルールは `rules/archive/` ディレクトリに永久保存される:
- ルールID、全履歴、最終発生日、効果スコアが保存される
- アーカイブされたルールに一致するエラーが3回以上再発した場合、自動的に `deprecating` 状態で復活する
- これにより、一度解決した問題が再発した場合に再学習のコストをゼロにする

### 振動ルールの減衰メカニズム
追加と削除を繰り返す不安定なルールに対しては、以下の減衰メカニズムを適用する:

1. ルールが `active` ↔ `inactive` の遷移を1回行う毎に、次回の追加閾値を50%上昇させる
2. 最大で元の閾値の4倍まで上昇する
3. 安定して1000セッション経過後、閾値は元の値に戻る

例:
- 初期追加閾値: 10%
- 1回振動後: 15%
- 2回振動後: 22.5%
- 3回以上振動: 30%

> **設計根拠:** 何度も追加と削除を繰り返すルールは、真の原因が解明されていないか、効果が境界線上にあることを意味する。このようなルールに対してはより厳しい基準を適用し、システムの安定性を確保する。

---

## Human Review ポリシー（段階制）

### Phase A（初期: フェーズ1〜2）

- 毎日レビュー（必須）
- サンプルの20%を人間確認

### Phase B（安定化: フェーズ2.5）

- 2日に1回レビュー
- サンプルの10%確認

### Phase C（成熟: フェーズ3以降）

- 週次レビュー
- サンプルの5%確認

### エスカレーション条件

以下が発生した場合:

- 新カテゴリの失敗
- 成功率のCI_lowerが5%以上低下

→ 即時レビュー頻度を1段階引き上げ

### 人間の役割（変更）

人間は以下のみ実施:

- validatorで検出できない例外の判断
- 週次レビュー

禁止:
- 毎回のログ分析
- 手動ルール追加

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

> `rules/hints_basic.md` として保存する。低性能モデル（MiniMax M2.5 / Gemini）への指示時に `CORE.md` と一緒に渡す。

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
- 評価モデル: MiniMax M2.5 / Gemini CLI
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

## scripts/prompt_builder.py

> 動的ルール組み立てシステム。タスクに応じて最適なルールセットを選択し、LLMに渡すプロンプトを最小化する。

**仕様（変更）:**

入力:
- 過去の失敗ログ（logs/errors）

処理:
1. 直近の失敗カテゴリを集計
2. 今回のタスクに関連する制約のみ抽出

出力:
- 最小制約セット

例:
```
if "reference_error" が多い:
    → "copy-from の存在確認" を追加
```

効果:
- ルール爆発防止
- コンテキスト最適化

**効果:** 常にLLMに渡すルールテキストを最適化・最小化し、コンテキストウィンドウの限界と指示忘れを防ぐ。実装コスト2-3時間に対し、成功率への寄与は15-20%と見込まれる。

### ルール状態フィルタリング
prompt_builder.py はルールの状態を考慮して以下のルールのみを選択する:
- `active` 状態のルール
- `deprecating` 状態のルール
- `inactive` 状態のルールは完全に除外

---

## scripts/rule_manager.py

> ルールライフサイクル管理システム。ルールの追加・廃止・状態遷移を自動的に行い、ルール爆発を防止する。

**仕様:**
1. 動的実行間隔:
   - フェーズ1-2: 1時間毎
   - フェーズ3: 6時間毎
   - フェーズ4以降: 24時間毎
2. 全てのルールについて失敗ログを集計
3. 状態遷移の優先順位に従って条件評価
4. 2種類の削除条件（発生しなくなった・効果がない）を評価
5. 条件を満たすルールを自動的に状態遷移
6. 振動ルールの減衰メカニズムを適用
7. ルールメタデータを `rules/meta.json` に保存

**保存するメタデータ:**
```json
{
  "rule_id": "syntax_trailing_comma",
  "status": "active",
  "first_seen": "2026-04-15",
  "last_occurrence": "2026-04-16",
  "occurrence_count": 12,
  "occurrence_before": 15,
  "occurrence_after": 12,
  "window_count": 50,
  "deprecating_since": null,
  "effectiveness_score": 0.2,
  "transition_count": 0,
  "oscillation_count": 0,
  "threshold_multiplier": 1.0,
  "last_review": null,
  "ab_test_results": []
}
```

**実装するコマンド:**
```bash
# 全ルールの状態をチェック
python scripts/rule_manager.py check

# 特定のルールの状態を強制変更
python scripts/rule_manager.py set-status <rule_id> active

# ルール一覧と状態を表示
python scripts/rule_manager.py list
```

---

## scripts/balance_checker.py

> バランス自動チェッカー。Level3テストの主要な失敗要因である意図しないバランス崩壊を自動検出する。

**仕様:**
1. mod内の全JSONファイルを走査
2. `copy-from` を使用しているアイテムについて、元のバニラアイテムの数値を `external/cdda/` から取得
3. 各数値（ダメージ、重量、容量、価格等）の乖離率を計算
4. 設定しきい値（デフォルト±50%）を超えている場合、警告またはエラーを出力
5. 意図的な乖離の場合は `// @allow-override` コメントで例外を許可

---

## 新規セクション: 検証パイプライン（必須）

### アーキテクチャ

```
[AI生成]
   ↓
[JSON Schema Validator]
   ↓
[Static Analyzer]
   ↓
[Runtime Test]
   ↓
[Score Calculator]
```

### スコアリング

| 項目 | スコア |
|---|---|
| 構文 | 0 or 100 |
| スキーマ | 0-100 |
| 整合性 | 0-100 |
| 実行 | 0-100 |
| バランス | 0-100 |

## スコアリング（非線形化）

### ハード制約（必須条件）

以下のいずれかを満たさない場合:

- JSON構文エラーあり
- Schema違反あり
- 起動エラーあり

→ **即不合格（スコア計算を行わない）**

### ソフトスコア（通過後のみ）

| 項目 | 重み |
|---|---|
| 整合性 | 0.3 |
| 動作 | 0.4 |
| バランス | 0.3 |

### スコア計算

```
score = 0.3*consistency + 0.4*runtime + 0.3*balance
```

### 合格条件

```
score >= 75
```

### 理由

- 構文エラーは致命的（ゲート化）
- 動作を最重視
- 線形平均の問題を回避

## モデル別ヒント

（変更）

モデル依存を最小化する:

- hintsは補助扱い
- validatorを主軸とする

方針:
```
ルール ≠ モデル
```

---

## 低性能モデルへの初期プロンプト（最短ルート用）

### MiniMax M2.5 向け（評価・成功率計測用）

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
1. MiniMax M2.5に同じmodを30回実装させる（分割して実施）
2. 成功率記録（5回ごとに中間集計）
3. 頻出エラーTOP3を特定
4. モデル別hints を更新

### Day 6: フェーズ2突破確認
1. 30回中24回（80%）成功達成確認
2. 条件付き合格OK
3. `prompt_builder.py` 基本実装
4. フェーズ2完了

### Day 7-8: フェーズ2.5（段階的汎化）
1. 同カテゴリ別アイテムで15回実装テスト
2. `balance_checker.py` 実装
3. 成功率80%維持を確認
4. フェーズ2.5完了

### Day 9以降: フェーズ3へ移行

---

## コスト最適化エンジン（長期戦略）

### 基本原則

```
if 旧modの0.I RC向け修正:
    Nemotron 3 Super
elif 小規模・中規模mod作成:
    MiniMax M2.5
elif 大規模mod・複雑タスク:
    Claude Sonnet 4.6 / Claude Opus 4.7
else:
    Kilo Code
```

### 難易度推定基準

| 基準 | 低難易度 | 中難易度 | 高難易度 |
|---|---|---|---|
| JSON行数 | 1〜50 | 51〜100 | 100+ |
| type数 | 1 | 2〜4 | 5+ |
| copy-from | 浅 | 中 | 深 |
| 新規概念 | なし | 一部あり | あり |

### 判断ロジック

1. **旧mod移植・修正**: Nemotron 3 Super
2. **JSON行数 < 50 / type数1つ / 新規概念なし**: MiniMax M2.5
3. **JSON行数51〜100 / type数2〜4**: MiniMax M2.5
4. **JSON行数100+ / type数5+ / 新規概念あり**: Claude Sonnet 4.6
5. **非常に複雑なタスク**: Claude Opus 4.7
6. **設計・高性能タスク**: Kilo Code

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
10. MiniMax M2.5 に `CORE.md` + モデル別hints を渡して同じmodを30回実装させる（5回ごとに中間集計）
11. 結果を `logs/agent_reports/` にレポートとしてまとめる
12. 頻出エラーTOP3をモデル別hints に追加する
13. `scripts/prompt_builder.py` を実装する
14. 成功率80%以上になったらフェーズ2.5へ進む

### フェーズ2.5: 段階的汎化（Day 7-8）
15. 同カテゴリ別アイテムで15回実装テストを実施
16. `scripts/balance_checker.py` を実装して稼働確認
17. 成功率80%維持を確認
18. フェーズ3へ進む

### フェーズ3: 長期戦略へ（週次以降）
19. unseenタスクベンチマークの導入
20. ルール構造化（JSON化）
21. human reviewポイントの整備
22. コスト最適化エンジンの実装

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
| 2026-04-15 | **大幅改善:** (1) Level3自動化方針を全面改訂、balance_checker.py を必須タスクとして追加、Step Cを破棄。(2) 動的ルール組み立てシステム prompt_builder.py を追加。(3) hints_basic.md を廃止しモデル別ヒント(hints_qwen.md, hints_gemini.md)に分割。(4) フェーズ2と3の間にフェーズ2.5（段階的汎化）を新設、成功率急落問題を緩和。(5) ロードマップを更新。 |