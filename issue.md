# 残る問題点・改善点

最終更新: 2026-09-14

## Critical Issues

### 3. design.md カバレッジ不足（解決済み）
- **ステータス:** 解決済み（2026-09-14）
- **重要度:** 中
- **詳細:**
  - 2026-09-14 時点: 24 mod 中 design.md が 24 件（`eoc_talk_test` と `wm_weapon_mastery` を D-3 で作成し穴埋め完了）
  - spec.md は新規システム3modのみの3件（`combat_stim` / `bone_armor` / `hedge_magic`）。小規模modの省略条件は `rules/CORE.md`（正本、日本語）に集約し `AGENTS.md` は英語mirror（D-2）。残件は E-8 で整理済み
- **解決案:**
  - 済み。spec 要否は `rules/CORE.md` の小規模mod定義（ID5個以下 + copy-fromのみ + 既存拡張 + 派生明確）に従う

## Minor Issues

### 4. ベンチマーク未整備
- **ステータス:** 一部解決（2026-09-14、F-2で土台のみ整備。測定スクリプトは未整備）
- **重要度:** 低
- **詳細:**
  - `benchmarks/` を性能測定専用と再定義し、評価タスク分類（`mods/seen/`・`mods/unseen/`）との二重 taxonomy を解消。旧 `benchmarks/{random,seen,unseen}/` は廃止（正本: `benchmarks/README.md`）
  - `pytest-benchmark` は導入しない（標準ライブラリで足りる間は依存を増やさない。CI の性能回帰ゲートが必要になったら再検討）
  - 測定スクリプト自体は未整備（必要時に `benchmarks/` 直下に追加）
- **解決案:**
  - 大規模 mod に対する処理時間の計測スクリプトが必要になったら `benchmarks/` 直下に置き、`benchmarks/README.md` から参照する

### 5. ドキュメント言語の混在
- **ステータス:** 解決済み（2026-09-14、F-3で日英併記を方針確定）
- **重要度:** 低
- **詳細:**
  - `AGENTS.md` は英語のエージェント入口、他文書（`README.md`・`cdda_mod_dev_plan.md`・`rules/`）は日本語正本、コードのコメント・CLIメッセージ・識別子は英語とする併記方針に確定（正本: `AGENTS.md` 言語節、`README.md` 既知の問題節）
  - 旧解決案（英語統一 or バイリンガル化）は方針確定により close
- **解決案:**
  - 済み。新規文書は併記方針に従うこと

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

### 9. 新規3modのLevel3検証が未実行
- **ステータス:** 未解決（2026-09-13 起票）
- **重要度:** 中
- **詳細:**
  - `mods/small/combat_stim` / `bone_armor` / `hedge_magic` は Level1（JSON構文）・Level2（CDDAエンジン読み込み、ERRORなし）のみ確認済み
  - Level3（ゲーム内でのスポーン・クラフト・発動・呪文習得などの動作確認）は**未実行**
  - 各 mod の `design.md` の完了条件にも「未実行（手動確認待ち）」と記載
- **解決案:**
  - CDDA を起動し、各 `design.md` の「テスト手順」に従って Level3 を実施する
  - 確認ポイント: combat_stim（効果付与と enchantment 反映）/ bone_armor（装備・クラフト反映）/ hedge_magic（呪文書からの習得と詠唱・効果付与）
  - 手順は `docs/level3_checklist.md` に機械可読チェックリストとして転記済み（2026-09-14、C-3）。Level3 9項目はすべて未実行（`grep -c "^- \[ \]" docs/level3_checklist.md` = 9）。実行時はチェックリストの `[ ]` → `[x]` と本節を連動更新する
  - Level3は必須（手動確認）。`templates/design_template.md` の完了条件と整合済み（E-8）。Level定義の正本は `rules/verification.md`

## アーカイブ（解決済み・E-8で移動）

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
  - 追加ジョブ: `validate` (`validate_mods.py` 全mod Level1検証 + ID重複チェックと `verify_patches.py` パッチ構造検証を統合、E-7で集約)
  - `requirements-dev.txt` により dev 依存バージョンを固定
- **解決案:**
  - 特になし。

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
