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

### recipe に `activity_level` が必須化（破壊的変更）
- `recipe` オブジェクトに `activity_level` フィールドが必須になった
- 省略するとゲーム起動時に `missing mandatory member "activity_level"` エラー
- 有効な値: `LIGHT_EXERCISE`, `BRISK_EXERCISE`, `MODERATE_EXERCISE`, `ACTIVE_EXERCISE`
- 旧modを移植するときは全ての recipe に `activity_level` を追加する
  ```json
  { "type": "recipe", "activity_level": "BRISK_EXERCISE", ... }
  ```

### その他（調査中）
- `external/cdda/doc/` の changelog やリリースノートを確認して随時追記する
- 変更確認コマンド:
  ```bash
  grep -r "TODO\|CHANGED\|DEPRECATED" external/cdda/doc/ | head -30
  ```

## バージョン確認方法
- `external/cdda/data/version.json` または `external/cdda/VERSION` を確認する