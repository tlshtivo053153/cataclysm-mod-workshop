# 検証ツール

このファイルは、CDDA mod開発で使う検証・チェックツールの詳細手順をまとめたものです。
簡易な概要は `CORE.md` を、初級者向け補足は `hints_basic.md` を参照してください。

---

## Level1: JSON構文チェック（validate.sh）

`scripts/validate.sh` は mod 内の全JSONファイルに対して構文チェックを行います。

### 特徴

| 項目 | 内容 |
|---|---|
| 入力 | ディレクトリパス（デフォルト: カレントディレクトリ） |
| 前提条件 | Python 3（`json.tool`） |
| 実行時間 | 1秒未満 |
| 検出範囲 | JSON構文エラーのみ（末尾カンマ、括弧の対応など） |

### 使い方

```bash
# modディレクトリ内で実行
bash scripts/validate.sh .

# または特定のmodディレクトリを指定
bash scripts/validate.sh mods/small/my_mod/
```

### 頻度

**編集のたびに実行してください。** 軽量なので頻繁に回すことを推奨します。

---

## Level2自動: mod読み込みチェック（check_mods.sh）

`scripts/check_mods.sh` は CDDA本体の `--check-mods` 機能を使い、modがゲームエンジンに正しく読み込まれるかを検証します。

### 特徴

| 項目 | 内容 |
|---|---|
| 入力 | `modinfo.json` 内の `"id"` フィールドの値（mod_id） |
| 前提条件 | `external/cdda/cataclysm-tiles` バイナリ + modが `external/cdda/mods/` に配置済み |
| 実行時間 | 最大30秒（タイムアウト設定あり） |
| 検出範囲 | 依存解決・copy-from存在・必須フィールド・型不一致などCDDAエンジンレベルのエラー |

### 前提条件の確認

1. `external/cdda/cataclysm-tiles` が存在することを確認
2. modが `external/cdda/mods/` に配置されていることを確認（配置手順は後述）

### 完全な手順（5ステップ）

```bash
# Step 1: JSON構文チェック（Level1）
bash scripts/validate.sh mods/small/my_mod/

# Step 2: modをCDDAのmods/に配置（symlink推奨）
bash scripts/link_mod_for_test.sh mods/small/my_mod/

# Step 3: mod_idを確認
cat mods/small/my_mod/modinfo.json | grep '"id"'
# 出力例: "id": "my_mod"

# Step 4: CDDA組み込みチェック（Level2）
bash scripts/check_mods.sh my_mod

# Step 5: エラー確認（debug.log）
cat external/cdda/config/debug.log
```

### mod_id の確認方法

`check_mods.sh` に渡すのは **ディレクトリ名ではなく、`modinfo.json` 内の `"id"` フィールドの値** です。

```bash
# modinfo.json から id を抽出
grep '"id"' mods/small/my_mod/modinfo.json
```

**注意**: `link_mod_for_test.sh` が作成するシンボリックリンク名はソースディレクトリのベース名です。ディレクトリ名と `modinfo.json` の `id` が一致しない場合があります。その場合は、`id` の値を `check_mods.sh` に渡してください。

例:
- ソースディレクトリ: `mods/small/MyCoolMod/` → リンク名: `MyCoolMod`
- modinfo.json の id: `"id": "my_cool_mod"` → 実行: `bash scripts/check_mods.sh my_cool_mod`

### 検出できるエラー

- `copy-from target not found` — 親IDが存在しない（スペルミスや依存mod未読み込み）
- `missing required field` / `missing mandatory member` — 必須フィールドの欠落
- `unknown type` — typeフィールドのスペルミス
- 依存modの解決失敗

### 検出できないエラー

- JSON構文エラー（`validate.sh` で事前にチェック）
- ゲーム内での実際の動作不具合（Level3で確認）
- バランス問題

### debug.log の読み方

`check_mods.sh` は実行前に `external/cdda/config/debug.log` をクリアします。
つまり、実行後の `debug.log` の内容は**すべてそのセッションのエラー**です。

```bash
# 最後のセッションのERROR行だけ確認
cat external/cdda/config/debug.log | grep ERROR
```

- `-----------------------------------------` でセッションが区切られます（最新セッションのみ読めばよい）
- `Stale game data detected` 警告は無視してよい

### 注意点

- **タイムアウト**: 30秒で強制終了します。大規模modや多数の依存がある場合は時間がかかることがあります
- **パフォーマンス**: `validate.sh` と比べて重い処理です。マイルストーン毎（機能完成時、PR前など）に実行してください
- **mod配置の更新**: ソースを修正したら、再度 `link_mod_for_test.sh` または `copy_mod_for_test.sh` を実行してCDDA側のmodを更新してください

---

## mod配置（link_mod_for_test.sh / copy_mod_for_test.sh）

modは `mods/<size>/<mod_name>/` に開発し、CDDAの `--check-mods` で検証するために `external/cdda/mods/` に配置する必要があります。

### symlink vs コピーの使い分け

| 方法 | スクリプト | 推奨ケース |
|---|---|---|
| シンボリックリンク | `link_mod_for_test.sh` | **通常はこちら**。ソース修正が即座に反映され、開発中の反復が快適 |
| コピー | `copy_mod_for_test.sh` | symlinkが使えない環境（Windows非Developerモード、特定のファイルシステム）、最終確認時 |

### 使い方

```bash
# symlinkで配置（推奨）
bash scripts/link_mod_for_test.sh mods/small/my_mod/

# コピーで配置
bash scripts/copy_mod_for_test.sh mods/small/my_mod/
```

どちらのスクリプトも、既存のリンク/ディレクトリがあれば自動で削除してから配置し直します。

---

## 検証フローまとめ

```
編集中 ──→ validate.sh（Level1: JSON構文）──→ 修正 ──→ 編集中
              ↑                                        |
              └────────────────────────────────────────┘
                （頻繁に実行、1秒未満）

機能完成時 ──→ link_mod_for_test.sh ──→ check_mods.sh（Level2: 読み込み）
                                              ↓
                                        debug.log確認
                                              ↓
                                        エラーあれば修正
                                              ↓
                                        エラーなし ──→ CDDA起動（Level3: 動作確認）
```
