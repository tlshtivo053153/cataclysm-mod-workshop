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

## debug.log の確認方法
- **末尾のセッションだけ読めばよい。** ファイル全体を読む必要はない
- セッションの区切りは `-----------------------------------------` 行
- 確認すべきは最後のセッション内の `ERROR` 行のみ
- `Stale game data detected` エラーが出た場合:
  - 原因: 前回実行時のキャッシュとJSONファイルのタイムスタンプが不一致
  - `check_mods.sh` は実行前に `flexcache` を自動削除するため、スクリプト経由では通常発生しない
  - `cataclysm-tiles` を直接実行した場合に発生することがある。その場合は `external/cdda/config/flexcache` を削除して再実行

### check_mods.sh 実行後の debug.log
`scripts/check_mods.sh` は実行前に `config/debug.log` をクリアします。
そのため、実行後の `external/cdda/config/debug.log` の内容は**すべてそのセッションのエラー**です。
以下で最新セッションのERROR行だけ確認できます:

```bash
cat external/cdda/config/debug.log | grep ERROR
```

`check_mods.sh` の実行結果（終了コード）と `debug.log` の両方を確認してください。

## recipe 作成時のチェックリスト
新しい recipe を書いたら、ゲームに読み込む前に以下を確認する:
- [ ] `"type": "recipe"` が正しく書かれているか
- [ ] `"activity_level"` フィールドがあるか（0.I RC で必須）
- [ ] `"result"` のアイテムIDが正しいか
- [ ] `"components"` 内の全IDが `external/cdda/data/json/` に存在するか。AMMOアイテム（`duct_tape`, `chem_carbide` 等）は `[ "id", N ]` でチャージ数指定（`ammo_type` 指定は不要）
- [ ] `"tools"` に `surface_heat` を使う場合、`["surface_heat", N, "LIST"]` 形式になっているか（`"C"` は無効）
- [ ] 同カテゴリ・同傾向の既存レシピを `external/cdda/data/json/recipes/` から1〜2個見つけ、`tools`・`qualities`・`components`・`difficulty`・`time` の設定を比較したか
- [ ] `scripts/validate.sh` を実行して構文エラーがないか
- [ ] `scripts/place_mod_for_test.sh --link` で mod を `external/cdda/mods/` に配置済みか
- [ ] `subcategory` が `"CSC_*_NESTED"` の場合、`type: "nested_category"` を定義し、`nested_category_data` にレシピIDを列挙しているか（詳細: `rules/patterns/recipe_nested.md`）
- [ ] `scripts/check_mods.sh <mod_id>` で CDDA 組み込みチェックを実行済みか（`mod_id` は `modinfo.json` の `"id"` 値）

## アイテムID設計の注意点
- **バニラに同じIDが存在する場合がある。** IDを決める前に必ず確認する:
  ```bash
  grep -r '"id": "作ろうとしているID"' external/cdda/data/json/
  ```
- 何も出力されなければそのIDは使える
- 出力があればバニラと衝突するため、プレフィックスを変えて別IDにする
- **計画書に記載する参照IDも存在確認する:** `copper_saw` のように、バニラに存在しないIDを計画書や根拠に記載しないようにする

## アイテム作成時のチェックリスト（0.I RC）
新しいアイテムを書いたら、以下を確認する:
- [ ] `ITEM` 型の場合、`subtypes` が正しく設定されているか（`TOOL`, `COMESTIBLE` 等）
- [ ] `name` の形式が subtype に合っているか
  - `TOOL` → `{"str": "..."}`
  - `COMESTIBLE`/`FOOD`/`DRINK` → `{"str_sp": "..."}`
- [ ] `phase: solid` や `phase` 未定義の固体アイテムに、`charges` を定義していないか（定義すると `charges defined but can not have any` 警告が出る）
- [ ] `material` フィールドの値がバニラの material ID として存在するか確認する:
  ```bash
  grep -r '"id": "meat"' external/cdda/data/json/materials.json
  ```
  - `meat` は material として定義されていない（食品アイテムIDとしては存在するが material ではない）

## Level2 と Level3 の違い（混同しない）
- **Level2** = ゲームが起動し、modの読み込みにエラーが出ない
  - 確認方法: debug.log の最新セッションに ERROR がないこと
- **Level3** = アイテムが実際にゲーム内で意図通りに動作する
  - 確認方法: デバッグメニューでスポーン、装備、クラフト等を手動で実施
  - Level2が通っても Level3 が失敗することがある（別の確認が必要）

## 成功判定（最短ルートの合否基準）
| レベル | 基準 | フェーズ2 | フェーズ3 |
|---|---|---|---|
| Level1 | JSON構文OK | 必須 | 必須 |
| Level2 | 起動OK | 必須 | 必須 |
| Level3 | 意図通り動作 | 不要 | 必須 |

### 条件付き合格（フェーズ2のみ）
- 1〜2回の軽微修正でLevel2に達すれば合格とする
- 修正コスト ≤ 2 = 合格