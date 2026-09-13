# cataclysm-mod-workshop

Cataclysm: Dark Days Ahead（CDDA）の mod 開発・移植を効率化するためのツールキットおよびナレッジベース。
AI エージェントを用いたハイブリッド開発ワークフローを採用し、機械的変換はスクリプトで、創造的デザインは AI で処理する。

> **内部パッケージ名:** `pyproject.toml` 上は `cdda-mod-framework` として管理されている。

## 主要機能

| 機能 | 説明 |
|---|---|
| **自動変換スクリプト** | 旧バージョン mod の機械的変換（アイテムタイプ統合、単位変換、フィールド削除など） |
| **検証ツール** | JSON 構文チェック（Level1）、CDDA エンジン読み込みチェック（Level2） |
| **ルールベース** | 命名規則、型別パターン、よくあるエラー対策、バージョン差分の知識集約 |
| **テンプレート** | mod 仕様書・設計書のテンプレート（`templates/`） |
| **パッチ管理** | 旧 mod 移植時の変更差分をパッチセットとして保存・管理 |

## ディレクトリ構成

```
cataclysm-mod-workshop/
├── external/
│   └── cdda/                  ← CDDA 本体（.gitignore 対象）
├── rules/                     ← ナレッジベース
│   ├── CORE.md                ← 基本ルール（全モデル必読）
│   ├── hints_basic.md         ← 低性能モデル向け補足ヒント
│   ├── version_diff.md        ← バージョン間の破壊的変更一覧
│   ├── common_errors.md       ← よくあるエラーと解決策
│   ├── verification.md        ← 検証ツール詳細手順
│   └── patterns/              ← 型別実装パターン集（17ファイル）
├── scripts/                   ← 自動化スクリプト
│   ├── validate.sh            ← JSON 構文チェック
│   ├── check_mods.sh          ← CDDA エンジン読み込みチェック
│   ├── place_mod_for_test.sh  ← mod 配置（統合版、--link/--copy）
│   ├── setup_venv.sh          ← Python 仮想環境セットアップ
│   ├── convert_item_types.py  ← アイテムタイプ統合
│   ├── add_activity_level.py  ← activity_level 追加
│   ├── convert_price.py       ← 価格文字列化
│   ├── remove_armor_bullet.py ← 防具フラグ削除
│   ├── remove_invalid_fields.py ← 無効フィールド削除
│   ├── revert_translation_errors.py ← 翻訳差分 revert（個別）
│   ├── revert_all_translations.py   ← 翻訳差分 revert（一括）
│   ├── summarize_debug_log.py ← debug.log 集計
│   ├── common.py              ← 変換スクリプト共通ライブラリ
│   ├── mapgen/                ← mapgen DSL コンパイラ（17ファイル）
│   └── tests/                 ← テスト群
├── mods/
│   ├── small/                 ← 小規模 mod（24件）
│   ├── medium/                ← 中規模 mod（予約）
│   ├── large/                 ← 大規模 mod（予約）
│   ├── seen/                  ← 学習済み mod（予約）
│   └── unseen/                ← 未知タスク（予約）
├── patches/                   ← 旧 mod 移植パッチセット
│   └── <mod_name>_<from>_<to>/
├── templates/
│   ├── spec_template.md       ← mod 仕様書テンプレート
│   └── design_template.md     ← mod 設計書テンプレート
├── benchmarks/                ← ベンチマーク（予約）
├── .github/workflows/
│   └── ci.yml                 ← CI パイプライン
├── logs/                      ← 作業ログ（.gitignore 対象）
├── pyproject.toml             ← Python プロジェクト設定
├── AGENTS.md                  ← AI エージェント向け指示書（英語）
├── .gitignore
└── issue.md                   ← 既知の問題・改善点
```

## セットアップ

### 前提条件

- **Python 3.10 以上**
- **CDDA 本体**: `external/cdda/` に配置する（バイナリ `cataclysm-tiles` およびデータファイルが含まれていること）

### CDDA 本体の配置

```bash
# external/cdda/ に CDDA を配置
cp -r /path/to/cdda external/cdda/
```

`external/cdda/` は `.gitignore` 対象のため、Git 管理外となる。

CDDA のソース更新時は `external/cdda/` を差し替え、必要に応じて `rules/version_diff.md` を更新する。

### Python 仮想環境

```bash
bash scripts/setup_venv.sh
source .venv/bin/activate
```

`setup_venv.sh` は `.venv/` を作成し、`black`、`ruff`、`pytest`、`mypy`、`pyyaml` をインストールする。

## 開発ワークフロー（新規 mod 作成）

新規 mod 作成は以下の 9 ステップで行う。詳細は `rules/CORE.md` を参照。

| Step | 内容 | 使用ツール |
|---|---|---|
| 1 | 仕様書作成 | `templates/spec_template.md` |
| 2 | 仕様書レビュー（AI 自己レビュー） | AI エージェント |
| 3 | 計画書作成 | `templates/design_template.md` |
| 4 | CDDA データとの整合性確認 | `external/cdda/data/json/` |
| 5 | 計画書レビュー（AI 自己レビュー） | AI エージェント |
| 6 | 実装 | modinfo.json, data/*.json |
| 7 | 読み込みエラー解消（Level2） | `check_mods.sh` |
| 8 | 動作確認（Level3） | CDDA 手動起動 |
| 9 | バランス調整 | 既存コンテンツとの比較 |

Step 1・2 は、新規定義 ID が 5 個以下で `copy-from` のみの小規模 mod では省略可能。

### Step 6〜9 のコマンド例

```bash
# 実装中は編集のたびに Level1 チェック
bash scripts/validate.sh mods/small/my_mod/

# 機能完成時に mod を CDDA に配置（symlink 推奨）
bash scripts/place_mod_for_test.sh --link mods/small/my_mod/

# Level2: CDDA エンジン読み込みチェック
bash scripts/check_mods.sh my_mod

# エラー確認
cat external/cdda/config/debug.log | grep ERROR

# Level3: CDDA を起動し、デバッグメニューで動作確認
```

## 移植ワークフロー（旧 mod 移植）

旧バージョンの mod を現行 CDDA に移植する手順。

```
1. 旧 mod を external/cdda/mods/ に配置
2. 機械的変換をスクリプトで一括処理
   - convert_item_types.py    → アイテムタイプ統合
   - add_activity_level.py    → activity_level 追加
   - convert_price.py         → price 文字列化
   - remove_armor_bullet.py   → 削除フラグ除去
   - remove_invalid_fields.py → 無効フィールド削除
3. validate.sh で JSON 構文チェック
4. ゲーム起動確認（Level2）
5. 残ったエラーは手動修正、または AI に設計判断を委ねる
6. 変更差分を patches/<mod_name>_<from>_<to>/ にパッチ形式で保存
```

各変換スクリプトの適用順序と対応関係は `patches/` 配下の `README.md` に記載する。
実例として `patches/Magiclysm_with_Random_Dungeons_0G_to_0I/` を参照。

## 検証

検証は 3 段階で行う。

| レベル | 内容 | ツール | 実行タイミング |
|---|---|---|---|
| **Level1** | JSON 構文チェック | `scripts/validate.sh` | 編集のたび（1 秒未満） |
| **Level2** | CDDA エンジン読み込みチェック | `scripts/check_mods.sh` | 機能完成時 |
| **Level3** | ゲーム内動作確認 | CDDA 手動起動 | 最終確認 |

### 検証フロー

```
編集 → validate.sh（Level1）→ place_mod_for_test.sh --link → check_mods.sh（Level2）
                                                              ↓
                                                        debug.log 確認
                                                              ↓
                                                       CDDA 起動（Level3）
```

Level2 実行には `external/cdda/cataclysm-tiles` バイナリが必須。
mod は事前に `place_mod_for_test.sh` で `external/cdda/mods/` に配置する必要がある。
詳細な手順は `rules/verification.md` を参照。

## 技術スタック

| 技術 | 用途 |
|---|---|
| **Python 3.10+** | 変換スクリプト、共通ライブラリ（`common.py`） |
| **Bash** | 検証スクリプト、mod 配置スクリプト |
| **JSON** | CDDA mod データ形式 |
| **CDDA 0.I RC** | ターゲットバージョン |
| **black / ruff** | Python コードフォーマット・リンター |
| **pytest** | テストフレームワーク |

## 既知の問題

詳細は `issue.md` を参照。

- **spec.md 未整備**: 21 mod 中 spec.md が 1 件も作成されていない
- **孤児ファイル・空ディレクトリ**: `mods/{medium,large,seen,unseen}` が実質的に空（`activity_map_magiclysm.json` は `patches/` に移動済み）
- **ドキュメント言語の混在**: `AGENTS.md`（英語）とルール群（日本語）で言語が分かれている
