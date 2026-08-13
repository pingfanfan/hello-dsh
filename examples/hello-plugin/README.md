# hello-plugin

一个能跑通的最小 DSH 插件，注册一个 `pingfan_hello` 工具。

**这份代码是实测跑通的**（DSH `0.1.0-rc.6`），不是从文档推的。

## 跑起来

```sh
# 生成 overlay（路径必须是绝对路径）
cat > cordis.yml <<YAML
- insert:
    - id: hello
      name: '$(pwd)/src/hello.ts'
YAML

# 加载并调用
DEEPSEEK_API_KEY=sk-xxx npx @deepseek-ai/dsh --profile headless \
  --patch ./cordis.yml "调用 pingfan_hello 工具，参数 who 填 test"
```

看到 `HELLO to test` 就成功了。

## 写这个插件时踩到的三个报错

完整说明见 [`dsh-first-plugin`](../../skills/dsh-first-plugin/SKILL.md) 技能。摘要：

| 报错 | 原因 | 修法 |
|---|---|---|
| `must declare output { schema, render }` | 工具注册必须声明 `output` | 补 `output.schema` 和 `output.render` |
| `parameters.who.required must be true when present` | `required` 只能填 `true` | 可选参数直接省略 `required` |
| `cannot get property "xxx" without inject` | 模块里有 `export default` | 删掉，只用命名导出 |

另外：`parameters` 是**扁平字段映射**，不是标准 JSON Schema；但 `output.schema` **是**标准 JSON Schema。两者形态不同。
