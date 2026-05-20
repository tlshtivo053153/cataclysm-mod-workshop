# modinfo.json テンプレート

mod を認識させるための最小構成と推奨構成。

## 最小構成

```json
[
  {
    "type": "MOD_INFO",
    "id": "my_unique_mod_id",
    "name": "My Mod Name",
    "description": "Short description of what this mod does.",
    "category": "content",
    "version": "0.1.0",
    "dependencies": ["dda"]
  }
]
```

## 推奨構成（多言語対応・メタ情報付き）

```json
[
  {
    "type": "MOD_INFO",
    "id": "my_unique_mod_id",
    "name": "My Mod Name",
    "description": "Detailed description.\nCan span multiple lines.",
    "category": "content",
    "version": "0.2.0",
    "author": "Your Name",
    "maintainers": ["Your Name", "Co-Maintainer"],
    "dependencies": ["dda"],
    "core": false,
    "obsolete": false
  }
]
```

## フィールド解説

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `type` | ○ | 常に `"MOD_INFO"` |
| `id` | ○ | 一意な識別子（スネークケース推奨） |
| `name` | ○ | 人間可読な mod 名 |
| `description` | ○ | 説明文 |
| `category` | ○ | `content`, `item_group`, `monster_group`, `building`, `vehicle` 等 |
| `version` | ○ | セマンティックバージョニング推奨 |
| `dependencies` | ○ | 依存 mod ID の配列。最低限 `["dda"]` が必要 |
| `author` | △ | 作者名 |
| `maintainers` | △ | 現在のメンテナ配列 |
| `core` | △ | `true` にするとコアデータとして扱われる |
| `obsolete` | △ | `true` にすると選択画面で非表示 |

## 注意点

- `id` は他の mod と衝突しないよう prefix を付ける（例: `mymod_item_name`）
- `dependencies` に `magiclysm` 等の他 mod を含める場合、その mod が有効でないとエラーになる
- `category` が不正だと mod 選択画面で正しく分類されない
