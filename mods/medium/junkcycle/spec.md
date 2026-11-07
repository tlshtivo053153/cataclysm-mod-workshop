## Mod仕様書: Junkcycle（廃材バイク）

### 背景・動機
- 既存の廃材部品modは部品単体で、車両を1台組む体験がない。
- 車両システムの拡張だけで完結できる実装型が `rules/patterns/vehicle_part.md` にある。
- 序盤に「廃材部品で移動手段を組む」体験を追加する。専用部品は低スキルで作れるが、完成にはバニラ駆動部品の溶接・mechanics 2が必要。

### 追加/変更内容（What）
- 含むもの:
  - 専用 vehicle_part 3種: `jk_wheel`（廃材ホイール）、`jk_saddle`（廃材サドル）、`jk_cargo`（簡易カーゴ）
  - 設置用 ITEM 3点: `jk_wheel_item`、`jk_saddle_item`、`jk_cargo_item`
  - レシピ 3点（`result` は上記 ITEM ID）
  - バニラ流用: `frame_wood` ×3、`wheel_mount_light[_steerable]`、`tank_small`、`controls`、`engine_1cyl`、`battery_motorbike_small`、`alternator_motorbike`、`muffler`
- 含まないもの:
  - 新mapgen、NPC、モンスター、シナリオ、職業
  - 専用フレーム、専用タンク、完成車 `type: "vehicle"` プロトタイプ
  - 電気版、装甲、武器、サイドカー、折りたたみ車両
  - 既存車両・既存レシピの改変（追加のみ）

### ゲームプレイへの影響（Why）
- 廃材集め→専用3種を低スキル（fabrication 1）で製作→バニラ駆動部品と組んで走行、の段階的進行になる。
- 専用3種の製作・装着は低スキル、修理は溶接不要（ホイール修理のみ mechanics 2 継承）。
- バニラ流用部品は通常要件（`frame_wood` は釘、`tank_small` はドリル、`controls` / `muffler` / マウントは溶接、`engine_1cyl` は mechanics 2）。完成車全体の無溶接化ではない。
- 新ゲームシステムは追加しない。既存 vehicle システムの拡張のみ。

### 成功基準
- 専用3種・4個（`jk_wheel` ×2、`jk_saddle` ×1、`jk_cargo` ×1）をクラフトできる。
- バニラ `frame_wood` ×3 から車両を組み、専用部品＋バニラ駆動部品を装着して給油・走行できる。
- 専用3種の製作・装着は低スキル。修理は溶接不要（ホイール修理は mechanics 2）。
- Level1（JSON構文）・Level2（ERRORなし）を通過する。
- Level3でフル組み立て・走行・給油・脱着・修理・セーブ/ロードを確認する。
- 実測最高速が `motorcycle_cross` 以下。超える場合は調整して再試験する。
- 専用部品の耐久がベース以下。完成車の耐久が `motorcycle_cross` より低い。
- 専用部品のレシピ素材コストがバニラ同等品以下。

### スコープ判断
- 中規模mod。新規ゲーム内ID 9（vehicle_part 3＋ITEM 3＋recipe 3。`result` 由来のrecipe IDを含む）のため、小規模mod免除（5 ID以下）の対象外。Step 1・2は省略しない。
