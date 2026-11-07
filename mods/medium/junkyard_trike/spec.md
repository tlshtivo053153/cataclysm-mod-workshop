## Mod仕様書: Junkyard Trike（廃材トライク）

### 背景・動機
- `junkcycle` は2輪バイク向けの部品mod。本modは3輪の荷運び車を組むための専用パーツキットを追加し、序盤〜中盤の輸送を成立させる。
- 専用2種は低スキル・無溶接で作れるが、耐久は低い。車体のバニラ部品は既存の溶接・工具要件をそのまま使う。

### 追加/変更内容（What）
- 含むもの:
  - 専用 vehicle_part 2種: `jt_cargo_bed`（大型荷台）、`jt_side_basket`（側面バスケット）
  - 設置ITEM 2点とレシピ 2点（`result` は対応するITEM ID）
  - 車体はバニラ部品を流用（`frame_wood` / `xlframe`、`wheel_mount_light[_steerable]`、`wheel_bicycle` / `wheel_motorbike`、`saddle`、`controls`、`engine_1cyl`、`tank_small`、`battery_motorbike_small`、`alternator_motorbike`、`muffler`）
- 含まないもの:
  - 新車両システム、`type: "vehicle"` の完成車プロトタイプ、`vehicle_group` 注入
  - トレーラー連結、装甲車、電気版、武器、サイドカー、前面ガード
  - 既存車両の改変

### ゲームプレイへの影響（Why）
- プレイヤーがバニラのフレームに専用パーツを組み、3輪の荷運び車を自作する。
- 専用2種は低スキル・無溶接・低耐久。車体のバニラ部品は既存の溶接要件を維持する（完成車全体の無溶接化ではない）。
- `junkcycle` とは独立して併用可能。既存 vehicle システムの拡張のみ。

### 成功基準
- 専用2種をクラフトし、バニラフレームに装着して3輪車を組める。
- 総積載 65 L。最高速は `motorcycle_3wheel` 以下。
- Level1（JSON構文）・Level2（ERRORなし）を通過する。
- Level3で組立・積載・走行・給油・脱着・修理・セーブ/ロードを確認する。

### スコープ判断
- 中規模mod。新規ゲーム内ID 6（vehicle_part 2＋ITEM 2＋recipe 2）のため、小規模mod免除（5 ID以下）の対象外。Step 1・2は省略しない。
