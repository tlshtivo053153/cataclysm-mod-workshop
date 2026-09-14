# 技術的負債の修正計画 (Tech Debt Remediation Plan)

最終更新: 2026-09-14 (レビュー反映版 v4・人間決定反映済み)
対象リポジトリ: `cdda_mod_framework`
運用方式: Ralph loop (`ralph.yml:16-18`: `prompt_file: PROMPT.md`, `completion_promise: LOOP_COMPLETE`, `max_iterations: 100`)。
1イテレーション = 1タスク。タスク完了ごとに検証コマンドを通し、未完なら次イテレーションへ。全タスク完了でのみ `LOOP_COMPLETE` を出力する。
タスク総数約26に対し `max_iterations: 100` は手戻りバッファ込みでも余裕がある。

## 0. Loop開始前の人間作業 (ブートストラップ・必須)

Ralph loopに入る前に人間が実行する (自律loopに任せない):

- [ ] H-1 `PROMPT.md` 等の追跡化【人間決定済: PROMPT+ralph+hats】: `git add -f PROMPT.md ralph.yml hats.yml` してloopの再現性を確保する。`opencode.json` は今回は含めない (秘匿サニタイズ未了のため。含める場合は `permission` 設定をサニタイズしてから)。
- [ ] H-2 方針決定タスクの事前承認【人間決定済】: C-2=(b) CIではスキップ明示、F-2=性能測定に特化。loopはこの決定に従い実装のみ行う (独断で変更しない)。
- [ ] H-3 `hats.yml` との優先関係確認【人間確認済】: `hats.yml` のbuilderは `task.done` 時に `LOOP_COMPLETE` をprintする指示があるが、本計画 §4-6 を優先し、全タスク完了時のみ出力する。部分完了での早期終了を禁止する。

## 1. 目的・スコープ・非目標

- 目的: Python / Shell・CI / ドキュメント・リポジトリ構成の3系統の技術的負債を、P0→P1→P2の順で解消し、CIをグリーンに保つ。
- スコープ: `scripts/` (Python+Shell、`setup_venv.sh`含む)、`scripts/mapgen/`、`scripts/tests/`、`pyproject.toml`、`requirements-dev.txt`、`.github/workflows/ci.yml`、`.gitignore`、`AGENTS.md`、`README.md`、`cdda_mod_dev_plan.md`、`rules/`、`templates/`、`issue.md`、`mods/`、`patches/`、`benchmarks/`、`logs/` の運用。
- 非目標: 新規modの追加、CDDAゲーム本体の改修、Level3 (ゲーム内手動確認) の自動化完成 (ハーネス土台までとする)。

## 2. ベースライン検証コマンド (全タスク共通)

各タスク着手前と完了後に実行し、結果を記録する:

```bash
.venv/bin/ruff check scripts/
.venv/bin/black --check scripts/
.venv/bin/pytest scripts/tests/ -q
.venv/bin/mypy scripts/
bash scripts/validate.sh mods/small
.venv/bin/python scripts/validate_mods.py
.venv/bin/python scripts/verify_patches.py
git status --porcelain   # exit 0固定なので「差分が意図通りか目視」が判定基準
git diff --stat
```

shellcheckについて: ローカル未導入の場合はスキップ可とし、その場合はCIのshell job緑をもって代替とする。成功基準は「shellcheckを除き全緑 + shellcheckはCI緑」とする。

## 3. 現状分析サマリ (エビデンス付き)

### 3.1 Python系

- P0-1 `mypy strict`形骸化: `pyproject.toml:57-100` で `strict=true` なのに `tests.*` + 移植系8モジュール (`convert_item_types`, `convert_price`, `add_activity_level`, `remove_armor_bullet`, `remove_invalid_fields`, `summarize_debug_log`, `revert_all_translations`, `revert_translation_errors`) が `ignore_errors=true`。参考値として `--config-file=/dev/null --strict` で46 errors/7 files相当 (mypy版依存のため、A-1で版数+全出力を記録すること。`requirements-dev.txt` は `mypy==2.1.0`)。
- P0-2 パッケージ構成破綻: `scripts/__init__.py` なし。`pyproject.toml:14-15` (`mapgen-compile = "mapgen.cli:main"`) + `:17-18` (`packages.find where=["scripts"]`) では `common.py` (トップレベルモジュール) が配布物に入らず、`mapgen/cli.py:12` の `from common import ...` がインストール環境で `ModuleNotFoundError`。現状は `scripts/tests/conftest.py:4-6` と `scripts/mapgen_compiler.py:4-6` の `sys.path.insert` で糊塗。なお安易な `scripts/__init__.py` 追加では解決しない (トップレベルモジュールは配布物に入らないため)。正解は `py-modules` 追加・srcレイアウト移行等のいずれか (B-2で決定)。
- P0-3 `run_standard_pipeline` (`scripts/common.py:323-361`) の不使用: `add_activity_level.py:55-81` と `remove_invalid_fields.py:187-216` が約25〜30行を再実装し、単一ファイル→ディレクトリ救済 (`common.py:352-353`) と `copy_unchanged` 引き回しが欠落。`mapgen/cli.py:139-192` も独自パイプライン。
- P1-1 exit code/`main`不統一 (以下はPython CLIのみの話。Shell側は `place_mod_for_test.sh` のexit 2、`check_mods.sh` の0-4独自体系が別途存在し §3.2で扱う): `-> None` + 内部`sys.exit(1)` 系 (`common.py:323`, `convert_price.py:130`, `summarize_debug_log.py:156`, 無注釈 `def main():` 系として `add_activity_level.py:55`, `convert_item_types.py:84`, `remove_armor_bullet.py:70`, `revert_all_translations.py:48`, `revert_translation_errors.py:56`, `remove_invalid_fields.py:187`) と `-> int` + `sys.exit(main())` 系 (`validate_mods.py:110,162-163`, `verify_patches.py:82,109-110`) が混在。`mapgen/cli.py:75,101,192` のみ `exit 2` (usage error) 使用。
- P1-2 エラー捕捉漏れ: `summarize_debug_log.py:170-187` (`PermissionError`/`UnicodeDecodeError`素通し、`--top`負数黙殺)、`mapgen/cli.py:48-75` (`_run_single_file` は `exists()` チェック済みだがTOCTOUレース + ディレクトリ指定時の `IsADirectoryError` 未処理、`_compile_doc` の `open()` 由来 `FileNotFoundError`/`UnicodeDecodeError` 素通し)、`validate_mods.py:98-102` (`subprocess.run` timeoutなし・`FileNotFoundError`無捕捉)。
- P1-3 定型文コピペ: `MAX_DEPTH = MAX_RECURSION_DEPTH` + 再帰ガード5〜7行が6ファイルに重複 (`convert_item_types.py:33,37-43` 他)。`deepcopy`+no-op比較も6ファイル8箇所に重複 (`add_activity_level:48`、`convert_item_types:70,76`、`remove_armor_bullet:51,58`、`remove_invalid_fields:170`、`revert_all:36`、`revert_errors:44`)。
- P1-4 型・docstring二極化: `convert_price.py` は完備 vs `convert_item_types.py:36,68,84`、`remove_armor_bullet.py:15,49,70` 他は無注釈・docstringなし。
- P2-1 テスト穴: `revert_all_translations.py` (53行)、`revert_translation_errors.py` (63行)、`verify_patches.py` (110行)、`validate_mods.py` (163行)、`mapgen/cli.py` (192行) に専用テストなし。`parser.py` (636行) 等は間接カバレッジのみ。カバレッジ計測自体なし。

### 3.2 Shell・CI・検証基盤系

- P0-4 Level2未配線: `scripts/check_mods.sh:1-266` は整備済みだが `.github/workflows/ci.yml:34-50` から未呼び出し。CIはLevel1までしか保証しない。原因は `external/cdda/` がgitignoreでCI実行不可のまま放置。
- P0-5 Level1が構文のみ: `scripts/validate.sh:23` は `python3 -m json.tool` のみ。`rules/CORE.md` の重要ルール (activity_level必須、`copy-from`実在等。行番号はドリフトするため `grep -n activity_level rules/CORE.md` で再確認) は未自動化。
- P0-6 Level3完全手動: `issue.md:87-95` の新規3mod (combat_stim/bone_armor/hedge_magic) がLevel3未実行のまま常態化。手順の機械可読化なし。
- P1-5 旧ラッパー延命: `copy_mod_for_test.sh:1-7` / `link_mod_for_test.sh:1-7` は `place_mod_for_test.sh` への7行execラッパー。`rules/verification.md:175` で削除予定と言いつつ期限なし、テスト (`test_shell_integration.py:77-91,177-189`) が延命。
- P1-6 `.bak`除外3重実装: `validate.sh:13`、`common.py:19-31`、`validate_mods.py:24-29`。
- P1-7 stderr/exit不統一: `check_mods.sh:89,94` と `place_mod_for_test.sh:49`、`validate.sh:16` がエラー出力をstdoutに。exit体系も `validate.sh`(0/1)、`place_mod_for_test.sh`(2あり)、`check_mods.sh`(0-4独自) でバラバラ。
- P1-8 CIの穴 (`ci.yml:1-50`): `permissions:`/`concurrency:`/`timeout-minutes:`なし、`workflow_dispatch`/`schedule`なし、カバレッジなし、shell jobキャッシュなし・apt毎回更新、checkout×4・setup-python×3の重複、成果物uploadなし。
- P1-9 bootstrap乖離: `requirements-dev.txt` (厳密pin。`PyYAML` 表記) vs `scripts/setup_venv.sh:21` (pinなし。`pyyaml` 表記も正規化対象)。shellcheckはCIのみでローカル未導入。
- P2-2 shebang不統一 (`#!/usr/bin/env bash` vs `#!/bin/bash`)、`place_mod_for_test.sh:13` のGNU-specific注意、CIログ肥大 (`validate_mods.py:95-107` が `validate.sh` 全行再表示、`--quiet`なし)。

### 3.3 ドキュメント・リポジトリ構成系

- P0-7 知識喪失: `.gitignore:2` `logs/` のため移植知見 + check logが管理外。`logs/.gitkeep` 自体がignoreされ死にファイル。`PROMPT.md`/`hats.yml`/`opencode.json`/`ralph.yml`/`.ralph/` も `.gitignore:13-17` で管理外のため、新規cloneで再現不能。加えて `.gitignore:11` の `.kilo/plans/` と `:13` の `.ralph/` は除外設定にも関わらず `git ls-files` では `.kilo/plans/*.md` 約20件と `.ralph/agent/scratchpad.md` が追跡済み (force-add混在)。追跡継続か除外徹底かをD-1で決定する。
- P0-8 ワークフロー矛盾: `AGENTS.md:20-23` (4手順) vs `README.md:99-109` / `cdda_mod_dev_plan.md:92-114` / `rules/CORE.md:13-86` (9ステップ)。spec/designレビューがスキップされる構造で `issue.md:32` の常態化と直結。
- P0-9 spec/design不足: 24mod中 `spec.md` 3件、`design.md` 22件 (`eoc_talk_test`、`wm_weapon_mastery`欠落)。免除根拠記録0件。
- P1-10 構成形骸化: `mods/{medium,large,seen,unseen}` は `.gitkeep` のみで実質不変。全24modが `mods/small/` に集中。`benchmarks/` は実質空 (`.gitkeep`のみ。`random/.gitkeep`・`seen/.gitkeep` は追跡済み、`unseen/.gitkeep` のみignoreで死にファイル)。`patches/` は単一事例のみでトップレベル規約なし。`mods/unseen/.gitkeep` の有無は `ls` で実測確認する。
- P1-11 `issue.md` 陳腐化: `#1,#2,#8` 解決済み残置、`README.md:191` (21mod中spec 0件) と `issue.md` (24mod中spec 3件) の数値矛盾、`design_template.md:44` (Level3任意) と `issue.md #9` (Level3中重要度) の矛盾。
- P1-12 検証ドキュメント5重複: Level1/2/3定義が `README`/`cdda_mod_dev_plan`/`CORE`/`verification.md`/`hints_basic.md` に分散。正本は `rules/verification.md` に一本化。`hints_basic.md:113-122` の「フェーズ2/3」は `cdda_mod_dev_plan.md:187` で削除済み概念を参照 (削除対象)。
- P2-3 表記ゆれ: 言語混在 (`AGENTS.md`英語 vs 他日本語)、プロジェクト名4分裂 (`cataclysm-mod-workshop` vs `cdda-mod-framework` vs `cdda-mod-dev/` vs `cdda_mod_framework`)、mapgen件数ドリフト (`README` 17 vs 実測。数え方は `ls scripts/mapgen/*.py | wc -l` で再測)、`AGENTS.md:65` 鮮度切れ (2026-07-22)。

## 4. タスク一覧 (全順序・逐次実行。並行実行禁止)

凡例: [ID] 内容 — 完了条件 — 検証。§0の人間作業完了後に A-1から順に1つずつ実行する。前提タスク未完のまま次に進まない。

### Phase A — 安全網 (最初に実行)

- [ ] A-1 ベースライン記録: §2のコマンド全実行結果 (成功/失敗含む) を作業ログに保存する。`logs/` への保存はD-1完了まで行わない (現状git管理外で消失するため。一時的に `/tmp/opencode/baseline_YYYY-MM-DD.md` 等に保存)。mypy版数と `--config-file=/dev/null --strict` の全出力も参考記録する。完了条件: 失敗項目リスト化。検証: ログファイル存在。
- [ ] A-2 CI最小硬化【人間決定: workflow_dispatch+scheduleはE-7で追加】: `ci.yml` に `permissions: contents: read`、`timeout-minutes` (例: 10)、`concurrency: {group, cancel-in-progress}` を追加する。`workflow_dispatch`/`schedule` はここでは追加せずE-7に回す。完了条件: YAML有効・既存job緑。検証: `git diff .github/workflows/ci.yml` + CI緑。
- [ ] A-3 カバレッジ計測開始 (前出し): `pytest-cov` を `requirements-dev.txt` に追加し、CIのpytestに `--cov=scripts --cov-report=term-missing` を追加する (閾値failは設けない)。完了条件: CIログにカバレッジ表が出る。検証: CIログ確認。本格的な穴埋めはE-4で行う。

### Phase B — Python P0 (B-2→B-1群→B-3の順。import解決を先にし手戻りを防ぐ)

- [ ] B-2 パッケージ構成修復: `pyproject.toml` の `packages.find`/`project.scripts` 修正 (`common` 配布漏れ解消のため `py-modules` 追加・srcレイアウト移行等のいずれかを選択)、`mapgen/cli.py`・`mapgen_compiler.py`・`conftest.py` の `sys.path` ハック削減、絶対/相対import方針の明文化。完了条件: `pip install -e .` 後に `mapgen-compile --help` と `.venv/bin/python -c "import common"` が成功。検証: 上記2コマンド + 既存テスト緑。
- [ ] B-1a 型付け (`convert_price`): 最も cleanなため最初に `ignore_errors` を外して `mypy scripts/` 緑化する。完了条件: override1件削除 + mypy緑。検証: `mypy scripts/` + `ruff` + `pytest`。
- [ ] B-1b 型付け (`summarize_debug_log`): `dict[str, dict]` 等の裸dictを `dict[str, Any]` 化しoverride削除。完了条件: 同上。検証: 同上。
- [ ] B-1c 型付け (`add_activity_level` + `remove_invalid_fields`): `main`含む。完了条件: override2件削除 + mypy緑。検証: 同上。
- [ ] B-1d 型付け (残り4モジュール: `convert_item_types`, `remove_armor_bullet`, `revert_all_translations`, `revert_translation_errors`): 完了条件: override4件削除 + mypy緑。検証: 同上。1イテレーションで終わらなければモジュール単位でさらに分割可。
- [ ] B-1e `tests.*` 方針決定: 厳格化するか `ignore_errors` 継続かを決定し、継続なら理由を `pyproject.toml` コメントに明記する。完了条件: 方針の文書化。検証: 目視レビュー。残存許容の記録場所は本ファイル §7 進捗ログとする。
- [ ] B-3 パイプライン統一: `add_activity_level.py` と `remove_invalid_fields.py` を `run_standard_pipeline` 使用に寄せる (追加オプションは `create_parser` 拡張で吸収)。単一ファイル→ディレクトリ救済の有無を仕様として統一。`mapgen/cli.py` との差異 (backup/check-only等) を `common.py` docstringに文書化。完了条件: 重複25〜30行×2の削除、振る舞い同等。検証: 該当スクリプトの既存テスト + 手動 `--help` 差分確認。

### Phase C — Shell・CI・検証 P0

- [ ] C-1 Level1内容検証の第一歩: `validate_mods.py` に `rules/CORE.md` から自動化容易な2〜3ルール (例: `activity_level`必須、`modinfo`必須フィールド、`copy-from`参照先の存在は警告レベル。行番号ではなくルール名で指定し `grep -n` で再確認) を追加する。完了条件: 違反fixtureでテストが赤→緑。検証: `pytest` + `.venv/bin/python scripts/validate_mods.py`。
- [ ] C-2 Level2のCI接続【人間決定: (b) CIではスキップ明示】: `check_mods.sh` をCIから呼ばない理由 (`external/cdda` 不在) を `ci.yml` コメントまたは `check_mods.sh --help` に明示し、手動実行手順を文書化する。(a) smokeモード・(c)単独文書化は採用しない。完了条件: 方針が可視化されている。検証: CIログまたは `--help`。
- [ ] C-3 Level3ハーネス土台: 新規3modの `design.md` テスト手順を機械可読チェックリスト (`docs/level3_checklist.md` 等。新設。`scripts/tests/` 直下は避ける) に転記し、未実行項目を `issue.md #9` と紐付けする。自動化は不要。完了条件: チェックリスト存在 + issue更新。検証: ファイル存在。

### Phase D — リポジトリ・ドキュメント P0

- [ ] D-1 `.gitignore`と知識保全: `logs/` 全除外をやめ、知見mdのみ追跡する方針を実装する。例:
  ```gitignore
  logs/*
  !logs/*.md
  !logs/.gitkeep
  check_*.log
  ```
  順序・`!`否定に注意し、`git check-ignore -v logs/foo.md logs/check_test.log` の期待出力例 (前者は無視されない、後者は無視される) まで確認する。`logs/.gitkeep` 復活。`.kilo/plans/` と `.ralph/` のforce-add混在は【人間決定: 除外徹底】で統一する (追跡済みファイルを `git rm --cached` し、必要なら別途エクスポート手順を整備)。`PROMPT.md`/`ralph.yml`/`hats.yml` の追跡化は §0 H-1済みか確認し、未済ならここで実施 (`opencode.json` は今回は対象外)。`benchmarks/unseen/` のignoreも同様に見直す。完了条件: `git check-ignore -v` が意図通り。検証: `git status` + `git ls-files logs benchmarks`。
- [ ] D-2 ワークフロー矛盾解消【人間決定: 9ステップに統一】: `AGENTS.md` (4手順) を `README`/`cdda_mod_dev_plan`/`CORE` (9ステップ) に寄せて統一する。`spec.md` 要否・免除条件 (`CORE.md` のID5個以下+copy-fromのみ規定) を明記し、`templates/` の使い分けを1箇所に集約。完了条件: 矛盾箇所の修正差分。検証: 目視レビュー。
- [ ] D-3 spec/design穴埋め: `eoc_talk_test` と `wm_weapon_mastery` の `design.md` 作成 (免除該当なら根拠を `issue.md` に記録して免除)。完了条件: `find mods/small -maxdepth 2 -name design.md | wc -l` が24 or 免除記録。検証: 上記コマンド。

### Phase E — P1 (順不同可、1つずつ)

- [ ] E-1 exit code/`main`統一: `-> int` + `sys.exit(main())` への寄せ方針決定。`mapgen/cli.py` の `exit 2` (usage error) と `exit 1` (processing error) の使い分けを全Python CLIに展開。完了条件: 全 `main` シグネチャ統一。検証: `mypy` + 境界テスト (存在しない入力でコード確認)。
- [ ] E-2 エラー捕捉: `summarize_debug_log.py:170-187`、`mapgen/cli.py:48-75`、`validate_mods.py:98-102` の素通し例外に捕捉+メッセージ追加 (`--top`負数はエラー化)。完了条件: 異常系テスト追加。検証: `pytest` 新規テスト。
- [ ] E-3 定型集約: 再帰ガード (`MAX_DEPTH`) と `deepcopy` no-op判定を `common.py` に集約し6ファイルから呼び出す。完了条件: 重複削除。検証: 全変換スクリプトテスト緑。
- [ ] E-4 テスト穴埋め: `test_revert_*`、`test_verify_patches`、`test_validate_mods` (単体レベル。現状はshell integration経由のみ)、`test_mapgen_cli` を新設。`parser.py` 等の分岐単体試験を最低1件ずつ追加。完了条件: 新規テストファイル存在 + A-3のカバレッジレポートで対象行が計測される。検証: `pytest --cov`。
- [ ] E-5 旧ラッパー廃止予告: `copy/link_mod_for_test.sh` に削除バージョン・期限を明記し、`test_shell_integration.py` を `place_mod_for_test.sh` 直呼びに移行。完了条件: テストが新経路。検証: `pytest scripts/tests/test_shell_integration.py`。
- [ ] E-6 `.bak`除外・stderr統一: 除外ロジックを `common._is_backup_path` に一本化 (`validate.sh` はPython呼び出し or 同一正規表現)。エラー出力は `>&2` に統一、exit体系を1文書 (`rules/verification.md` 等。正本はここに一本化) に集約。完了条件: 差分確認。検証: `shellcheck` + 手動エラー出力確認。
- [ ] E-7 CI拡充+bootstrap統一【人間決定: workflow_dispatch+schedule追加】: `workflow_dispatch` (手動実行) と `schedule` (週次等) を追加し、pipキャッシュの全job化、shell jobのaptキャッシュor版pin、job重複削減、成果物upload (検証ログ) を行う。`setup_venv.sh` を `requirements-dev.txt` のpinと一致させ (表記 `PyYAML`/`pyyaml` も正規化)、shellcheckをローカル手順に追加。完了条件: CI緑 + ローカル再現手順文書化。検証: CI実行。
- [ ] E-8 `issue.md`・検証ドキュメント整理: 解決済み (`#1,#2,#8`) をアーカイブ節へ移動、数値矛盾 (`README:191` vs 実測) 修正、`design_template` (Level3任意) と `issue #9` の矛盾解消、Level定義の正本を `rules/verification.md` に一本化し他から参照、「フェーズ2/3」残骸削除 (`grep -rn "フェーズ2" rules/` ヒットゼロ)。完了条件: 目視レビュー。検証: 上記grep等。

### Phase F — P2 (余裕があれば)

- [ ] F-1 shebang/`--quiet`/可搬性: shebang統一、GNU-specific箇所のガード、`validate_mods.py --quiet` 追加。
- [ ] F-2 ベンチマーク土台【人間決定: 性能測定に特化】: `benchmarks/` を性能測定用と再定義し (評価タスク用は `mods/seen,unseen` 側に分離)、`mods/seen,unseen` との二重taxonomyを解消する。空ディレクトリに `.gitkeep` + README追加、`pytest-benchmark` 導入是非決定。
- [ ] F-3 表記ゆれ: プロジェクト名統一、言語方針決定 (全面英語化 or 日英併記)、`AGENTS.md` の Mapgen列挙更新・鮮度日付更新、`cdda_mod_dev_plan.md` 更新履歴追記。

## 5. 実行ルール (Ralph用)

1. 1イテレーションで1タスクのみ着手する。複数タスクの同時着手禁止 (Phase見出しの「並行可」表記は廃止。全順序で実行する)。
2. 着手前に §2 の該当検証を実行し、着手後に再実行して差分を示す。
3. テストがない変更にはテストを追加する (A-3の方針に沿う)。
4. 破壊的変更 (D-1のgitignore変更、B-2のパッケージ変更等) は `git status/diff` を必ず確認し、意図しないファイルを含めない。
5. 1タスク完了ごとに進捗を `issue.md` (Last updated更新) と本ファイル §7 進捗ログ追記で反映する (チェックボックス `[ ]`→`[x]` 更新も行う)。
6. コミット前に、複数のsubagentで多角的にレビューする (必須)。手順:
   - Taskツールで最低3視点のsubagentを並行起動する。視点例: (a)正しさ・仕様合致 (§3・§4完了条件との照合)、(b)回帰・セキュリティ・破壊的変更 (`git diff`・§2検証・意図しないファイル混入)、(c)テスト・ドキュメント整合 (新規テスト有無、カバレッジ、関連md更新)。
   - 各subagentには `git diff` (+必要に応じ `git status --porcelain`) を渡し、指摘を優先度付き箇条書きで返させる。コード変更自体はさせない (レビューのみ)。
   - P0指摘 (誤動作・検証失敗・仕様逸脱・秘匿混入等) が1件でもあればコミット禁止。修正→§2再検証→再レビューを行う。P1/P2のみ残存の場合は `issue.md` または §7 に記録してコミット可。
   - レビュー結果サマリ (視点×件数・対応内容) を §7 進捗ログに1行以上残す。
7. `hats.yml` の指示より本計画を優先する。全タスク完了時のみ最終行に `LOOP_COMPLETE` と出力する。未完なら出力しない。

## 6. 完了定義 (Definition of Done)

- Phase A〜D (P0) がすべて完了し、§2の検証が全緑 (shellcheckはCI緑で可)。
- `pyproject.toml` の `ignore_errors` がB-1群の計画通りに減少 (ゼロでなくとも可。残存理由は §7 進捗ログに記録すること)。
- `pip install -e .` 後の `mapgen-compile --help` 成功。
- `logs/*.md` と再現に必要な運用ファイルがgit追跡化され、`git check-ignore` が意図通り。
- ワークフロー矛盾・spec/design穴が解消 (or 免除記録)。
- Phase E (P1) が完了 or 残タスクが `issue.md` に再登録済み。
- 最終行に `LOOP_COMPLETE`。

---

## 7. 進捗ログ (各イテレーションで追記。残存 `ignore_errors` の理由もここに記録)

- 2026-09-14: 計画初版作成 (3系統subagent調査を統合)。
- 2026-09-14: レビュー反映 v2 — subagentレビュー (P0 8件・P1 14件・P2 9件) を反映。B-1分割、 B-2先行、 D-1ブートストラップ分離 (§0)、チェックボックス化、§2検証基準明確化、typo修正 (T-D1→D-1)、hats優先関係明記、A-3カバレッジ前出し、H-2人間承認明示、件数訂正 (deepcopy 6ファイル8箇所、checkout×4/setup-python×3) 等。
- 2026-09-14: 人間決定反映 v3 — H-1=PROMPT+ralph+hats追跡化 (opencode.json除外)、C-2=(b)スキップ明示、F-2=性能測定特化、A-2→E-7でworkflow_dispatch+schedule追加、D-1=除外徹底、D-2=9ステップ統一、H-3=本計画優先を確認。
- 2026-09-14: v4 — §5-6にコミット前マルチsubagentレビュー (3視点並行・P0残存時コミット禁止・§7記録) を追加。
