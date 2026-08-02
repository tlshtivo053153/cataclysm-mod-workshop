# 残る問題点・改善点

最終更新: 2026-08-02

## Critical Issues

### 1. テストの不足（解決済み）
- **ステータス:** 解決済み（2026-07-22）
- **重要度:** 高
- **詳細:**
  - `scripts/tests/` に約 3,260 行のテストが整備された（common.py、変換スクリプト、mapgen サブシステム、summarize_debug_log.py の 19 テストを含む）
- **解決案:**
  - 特になし。全スクリプトのテストが作成済み。

### 2. CI/CD の導入（依存固定・マトリクス化・mod検証追加により強化）
- **ステータス:** 解決済み（2026-08-01 更新）
- **重要度:** 高
- **詳細:**
  - `.github/workflows/ci.yml` が存在し、ruff + black + pytest + mypy + shellcheck を実行
  - Python 系: Python 3.10/3.11/3.12/3.13 マトリクス、ruff check, black --check, pytest, mypy
  - Shell 系: shellcheck
  - 追加ジョブ: `validate-mods` (全mod Level1検証 + ID重複チェック)、`verify-patches` (パッチ構造検証)
  - `requirements-dev.txt` により dev 依存バージョンを固定
- **解決案:**
  - 特になし。

### 3. design.md カバレッジ不足（spec.md 未整備に置換）
- **ステータス:** 未解決
- **重要度:** 中
- **詳細:**
  - 21 mod 中 spec.md が 0 件、design.md が 19 件（`eoc_talk_test` と `wm_weapon_mastery` が未作成）
  - `cdda_mod_dev_plan.md` のワークフローに反する運用が常態化している
- **解決案:**
  - spec.md の要否をワークフローに明記（免除条件または強制のいずれか）
  - 未作成の design.md 2件を作成

## Minor Issues

### 4. ベンチマーク未整備
- **ステータス:** 未解決
- **重要度:** 低
- **詳細:**
  - `benchmarks/` に `random/`、`seen/`、`unseen/` のディレクトリが存在するが実質的な内容なし
  - スクリプトのパフォーマンス測定基盤がない
- **解決案:**
  - 大規模 mod に対する処理時間のベンチマークスクリプトを作成

### 5. ドキュメント言語の混在
- **ステータス:** 未解決
- **重要度:** 低
- **詳細:**
  - `AGENTS.md` は英語、ルール群（`rules/`）は日本語で記述されている
  - AI モデルや国際的コントリビューターにとって障壁となる
- **解決案:**
  - 全ドキュメントの英語への統一、または全ファイルのバイリンガル化

### 6. 孤児ファイル・ディレクトリ
- **ステータス:** 一部解決（2026-08-01 更新）
- **重要度:** 低
- **詳細:**
  - `scripts/activity_map_magiclysm.json` → `patches/Magiclysm_with_Random_Dungeons_0G_to_0I/` に移動済み（移植用設定ファイル）
  - `logs/` が gitignore されているが知識成果物（移植ログ）が置かれ git 管理不能
  - `mods/{medium,large,seen,unseen}` が実質的に空
- **解決案:**
  - logs/ 運用方針の決定、空ディレクトリの .gitkeep 配置検討

### 7. issue.md の自己記述更新
- **ステータス:** 一部解決
- **重要度:** 低
- **詳細:**
  - 2026-07-22 に現状反映の全面改訂を実施
  - プロジェクトの進捗に合わせて本ファイルも定期的な見直しが必要
- **解決案:**
  - 月次での issue.md レビューをワークフローに組み込む

### 8. 移植スクリプトの exit code 仕様統一（解決済み）
- **ステータス:** 解決済み（2026-08-02）
- **重要度:** 低
- **詳細:**
  - 従来は processor が None を返す（変更対象なし）ファイルも「失敗」扱いで exit 1 になっていた
  - `common.ProcessResult` の導入により処理成功・スキップ・失敗を分離し、スキップは exit 0、失敗のみ exit 1 に統一
  - 対象: `run_standard_pipeline` 利用スクリプト（convert_item_types / remove_armor_bullet / revert_all_translations / revert_translation_errors）および convert_price.py
  - 仕様は `common.py` の `run_standard_pipeline` docstring に明記済み
- **解決案:**
  - 特になし
