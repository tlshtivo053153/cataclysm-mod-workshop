# CDDA Mod開発計画

## 1. 目的

AIエージェントを用いてCataclysm: DDAのmodを開発し、旧mod移植・小規模mod作成からノウハウを蓄積する。

## 2. ターゲットバージョン

| 種別 | バージョン | 備考 |
|---|---|---|
| 安定版 | 0.H "Herbert" | 2025年8月リリース |
| **ターゲット** | **0.I RC** | 仕様固定済み。バグ修正のみ |
| 実験的ビルド | experimental | 毎日更新。破壊的変更あり |

**本プロジェクトは 0.I RC をターゲットとする。**
実験的ビルドへの対応は `rules/version_diff.md` に記録し、後続フェーズで対応する。

### CDDAソースの配置

`external/cdda/` にCDDAのファイルを配置する（`.gitignore` 対象）。
- `external/cdda/data/json/` → アイテムIDやフラグの確認用
- `external/cdda/data/mods/` → 同梱modのサンプル
- `external/cdda/doc/JSON/JSON_INFO.md` → 全JSONフィールドのリファレンス

> **注意:** `external/cdda/` はGit管理から除外する。CDDAのバージョンアップ時はこのディレクトリを差し替えて `rules/version_diff.md` を更新する。

## 3. 開発原則

1. **設計・計画を先に行い、その後に実装を開始する**
2. **機械的変換はスクリプトで、創造的デザインはAIで**（ハイブリッドアプローチ）
3. `external/cdda/` のソースを常に参照して命名・構造の正確性を担保する
4. 問題が発生した場合は `logs/` にログを残す
5. ルール管理は手動（Markdownの編集）に統一する
6. 使えるモデルで適宜実行し、エラーが多ければ高性能モデルに投げる

## 4. ディレクトリ構成

```
cataclysm-mod-workshop/
├── external/
│   └── cdda/               ← CDDAソース（gitignore対象）
├── rules/                  ← ノウハウ蓄積
│   ├── CORE.md             ← 基本ルール（全モデル必読）
│   ├── hints_basic.md      ← 低性能モデル向け補足ヒント
│   ├── version_diff.md     ← バージョン差分（0.G→0.H→0.I等）
│   ├── common_errors.md    ← よくあるエラーと解決策
│   └── patterns/           ← 各種パターン集（随時追加）
├── scripts/                ← 自動化スクリプト
│   ├── validate.sh         ← JSON構文チェック
│   ├── check_mods.sh       ← mod確認補助
│   ├── place_mod_for_test.sh   ← mod配置（テスト用、--linkでsymlink）
│   ├── convert_item_types.py   ← 旧mod移植: アイテムタイプ変換
│   ├── add_activity_level.py   ← 旧mod移植: activity_level追加
│   ├── remove_invalid_fields.py ← 旧mod移植: 無効フィールド削除
│   ├── convert_price.py        ← 旧mod移植: 価格文字列化
│   ├── remove_armor_bullet.py  ← 旧mod移植: 防具フラグ削除
│   ├── revert_translation_errors.py ← 翻訳差分revert（個別）
│   └── revert_all_translations.py   ← 翻訳差分revert（一括）
├── mods/
│   ├── small/              ← 小規模mod
│   ├── medium/             ← 中規模mod
│   ├── large/              ← 大規模mod
│   ├── seen/               ← 学習済みmod
│   └── unseen/             ← 未知タスク
├── benchmarks/             ← 性能測定専用（評価タスクは mods/seen,unseen。詳細は benchmarks/README.md）
├── logs/                   ← 作業ログ（フラット構造）
├── patches/                ← 旧mod移植のパッチセット
│   └── <mod_name>_<from>_<to>/
│       ├── 01_xxx.patch
│       └── README.md
├── templates/
│   ├── spec_template.md    ← mod仕様書テンプレート
│   └── design_template.md  ← mod設計書テンプレート
└── .gitignore
```

### 移植済みmodの配置方針

- **原則:** 移植済みmodは `mods/` 配下に配置し、Git管理対象とする
- **例外（大規模旧mod移植）:** 変更差分が巨大で、かつ `external/cdda/mods/` 内に旧バージョンが存在する場合、変更差分を `patches/` にパッチ形式で保存する
  - ベースライン: `external/cdda/mods/` 内の旧バージョン（`.gitignore` 対象）
  - パッチ格納先: `patches/<mod_name>_<from>_<to>/`
  - パッチは順次適用を前提とし、`README.md` で適用順序と手順を明記する
- **テスト時:** `scripts/place_mod_for_test.sh [--link]` を使用し、パッチ適用後のディレクトリを `external/cdda/mods/` へ一時的に反映する

## 5. 作業フロー

### 新規mod作成

```
Step 1: 仕様書作成（小規模modは省略可）
  └── templates/spec_template.md を使用
  └── mods/<size>/<mod_name>/spec.md
Step 2: 仕様書レビュー（AI自己レビュー）
  └── スコープ・矛盾点の洗い出し
Step 3: 計画書作成
  └── templates/design_template.md を使用
  └── mods/<size>/<mod_name>/design.md
Step 4: CDDAデータとの整合性確認
  └── external/cdda/data/json/ でID・フラグ・値を実在確認
Step 5: 計画書レビュー（AI自己レビュー）
  └── ID命名・依存関係・実装後修正コストの洗い出し
Step 6: AIエージェントで実装
  └── modinfo.json, data/*.json
  └── 編集のたびに validate.sh（Level1）
Step 7: 読み込みエラー解消（Level2）
  └── place_mod_for_test.sh --link → check_mods.sh
Step 8: 動作確認（Level3）
  └── CDDA起動、デバッグメニューでスポーン・クラフト確認
Step 9: バランス調整
  └── 既存コンテンツとの比較、数値調整
```

詳細な手順・プロンプト例・チェックリストは `rules/CORE.md` を参照。
小規模modの定義（Step 1・2省略条件）も `rules/CORE.md` に記載。

### 検証レベル

| レベル | 内容 | 必須 | 対応ステップ |
|---|---|---|---|
| Level1 | JSON構文OK（`scripts/validate.sh`） | 必須 | Step 6（実装中に頻回実行） |
| Level2 | ゲーム起動OK（mod有効化時エラーなし） | 必須 | Step 7 |
| Level3 | 意図通り動作（スポーン・クラフト・バランス等） | 必須（手動確認） | Step 8〜9 |

Level1/2/3の定義の正本は `rules/verification.md` とし、本表は概要とする。

### ルール追加・削除の閾値

- **追加:** 同じエラーが3回以上発生した場合 → `rules/common_errors.md` に追記
- **削除:** 該当エラーが直近10回の試行で0回、かつルール追加後も改善が見られない場合 → 手動で削除

## 6. 旧mod移植フロー

旧mod移植は「機械的変換はスクリプトで、創造的デザインはAIで」というハイブリッドアプローチとする。

### ステップ

```
1. 旧modを external/cdda/mods/ に配置
2. 機械的変換をスクリプトで一括処理
   - convert_item_types.py    → アイテムタイプ統合
   - add_activity_level.py    → activity_level追加
   - convert_price.py         → price文字列化
   - remove_armor_bullet.py   → 削除されたフラグ除去
   - remove_invalid_fields.py → 無効フィールド削除
3. validate.sh でJSON構文チェック
4. ゲーム起動確認（Level2）
5. 残ったエラーは手動修正、またはAIに設計判断を委ねる
6. 変更差分を patches/<mod_name>_<from>_<to>/ にパッチ形式で保存
```

### パッチ運用の例

`patches/Magiclysm_with_Random_Dungeons_0G_to_0I/` を参照。
パッチは `01_item_types.patch` → `02_activity_level.patch` → ... の順に適用する。
各パッチの生成元となったスクリプト名と対応関係を `README.md` に記載する。

## 7. ルールファイル

ルールファイルの詳細は各ファイルを直接参照すること。

| ファイル | 内容 | 参照先 |
|---|---|---|
| `rules/CORE.md` | 基本ルール（命名規則、単位、copy-from等） | 全モデル必読 |
| `rules/hints_basic.md` | 低性能モデル向けの具体的な手順 | CORE.md と併用 |
| `rules/version_diff.md` | バージョン間の破壊的変更一覧 | 旧mod移植時必読 |
| `rules/common_errors.md` | よくあるエラーと解決策 | 随時更新 |

## 8. コスト最適化

モデル選択は以下の簡易フローとする：

```
1. 使えるモデルで適宜実行
2. エラーが多い・複雑な設計判断が必要 → 高性能モデル（Kilo Code等）に投げる
3. 機械的変換 → スクリプトで処理
```

無料モデル（OpenRouter等）で機械的な修正を行い、高性能モデルは設計レビュー・難問対応に留める。

## 9. 更新履歴

| 日付 | 更新内容 |
|---|---|
| 2026-04-15 | 初版作成 |
| 2026-04-15 | validate.sh のサブシェルバグ修正、フェーズ2評価回数変更等 |
| 2026-05-19 | **大幅改訂:** 統計的手法・rule_manager.py・prompt_builder.py・balance_checker.pyを削除。スクリプト優先のハイブリッドアプローチに整理。計画書を1500行→約300行に圧縮。 |
| 2026-05-22 | **開発フロー9ステップ化:** 仕様書→レビュー→計画書→レビューの2段階設計を導入。`templates/spec_template.md` 新規作成。`rules/CORE.md` と `cdda_mod_dev_plan.md` を9ステップ形式に更新。バランス調整・小規模mod定義・AIレビュープロンプト例を追加。 |
| 2026-09-14 | **技術的負債の是正 (PROMPT.md 計画 A〜F):** Python型付け・パイプライン統一 (B)、Level1〜3検証基盤 (C)、`.gitignore` 保全・9ステップ統一・design穴埋め (D)、exit/エラー/テスト/CI整理 (E)、shebang・ベンチマーク・表記ゆれ是正 (F)。名称対応表は `README.md` が正本、言語は日英併記 (`AGENTS.md` 英語・他日本語)、検証レベル定義の正本は `rules/verification.md`。 |
