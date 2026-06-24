# plugin-creator 脚本说明

## publish.py

发布插件到 claude-code-plugins-plus 市场。

```bash
python scripts/publish.py --plugin-path ./my-plugin
python scripts/publish.py --plugin-path ./my-plugin --category productivity
```

参数：
- `--plugin-path`: 插件路径（必需）
- `--category`: 分类（默认: productivity）
- `--no-pr`: 只提交不创建 PR
- `--message`: 提交信息

---

## validate_plugin.py

验证插件结构和 plugin.json。

```bash
python scripts/validate_plugin.py ./my-plugin
```

---

## quick_validate.py

快速验证插件结构。

```python
from quick_validate import validate_plugin

is_valid, message = validate_plugin("./my-plugin")
```
