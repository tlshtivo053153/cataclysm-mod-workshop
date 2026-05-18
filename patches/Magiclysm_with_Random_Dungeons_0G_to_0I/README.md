# Magiclysm_with_Random_Dungeons 0G → 0I パッチセット

## 適用順序

1. `01_item_types.patch` — アイテムタイプ統合（AMMO→ITEM 等）
2. `02_activity_level.patch` — レシピへの activity_level 追加
3. `03_price_conversion.patch` — price/price_postapoc の文字列化
4. `04_remove_armor_enchants.patch` — ARMOR_BALLISTIC / ARMOR_BULLET 削除
5. `05_remove_invalid_fields.patch` — 無効フィールド削除
6. `06_manual_fixes.patch` — その他の手動修正（名称形式、special_attacks、see_cost、EOC、field_type、rot_spawn、flags.json 等）

## 適用方法

```bash
cp -r external/cdda/mods/Magiclysm_with_Random_Dungeons-0G /tmp/mod_0i
for p in patches/Magiclysm_with_Random_Dungeons_0G_to_0I/*.patch; do
    patch -d /tmp/mod_0i -p0 < "$p"
done
```

## 検証

```bash
bash scripts/validate.sh /tmp/mod_0i
```

## 注意事項

- パッチは順次適用を前提としています。個別に適用すると行番号ずれで失敗する可能性があります。
- ベースラインは `external/cdda/mods/Magiclysm_with_Random_Dungeons-0G/` です。
