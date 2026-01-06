# Jinja2 模板引擎重构说明

## 概述

已成功将 `render.py` 从硬编码的模板字符串重构为使用 Jinja2 模板引擎的架构。

## 变更内容

### 1. 新增文件

#### `src/fastapi_voyager/render_style.py`
- **ColorScheme**: 颜色配置类（节点、链接、文本颜色）
- **GraphvizStyle**: Graphviz 样式配置类（字体、布局、链接样式）
- **RenderConfig**: 完整的渲染配置类

#### 模板文件
```
templates/
├── dot/                     # DOT 格式模板
│   ├── digraph.j2          # 主图模板
│   ├── tag_node.j2         # 标签节点
│   ├── schema_node.j2      # Schema 节点
│   ├── route_node.j2       # 路由节点
│   ├── cluster.j2          # 集群模板
│   ├── cluster_container.j2 # 容器集群
│   └── link.j2             # 链接模板
└── html/                    # HTML 格式模板
    ├── schema_table.j2     # Schema 表格
    ├── schema_header.j2    # 表格头部
    ├── schema_field_row.j2 # 字段行
    ├── pydantic_meta.j2    # Pydantic 元数据
    └── colored_text.j2     # 彩色文本
```

### 2. 重构文件

#### `src/fastapi_voyager/render.py`
- **新增 TemplateRenderer 类**: Jinja2 环境管理和模板渲染
- **重构 Renderer 类**:
  - 使用模板渲染替代字符串拼接
  - 分离关注点（格式化、渲染、配置）
  - 保持公共 API 不变，向后兼容

### 3. 依赖更新

#### `pyproject.toml`
```toml
dependencies = [
  "fastapi>=0.110",
  "pydantic-resolve>=2.4.3",
  "jinja2>=3.0.0"  # 新增
]
```

## 架构优势

### 1. **关注点分离**
- **逻辑层**: Renderer 类处理业务逻辑
- **视图层**: Jinja2 模板处理格式化
- **配置层**: render_style.py 管理样式常量

### 2. **可维护性提升**
- ✅ 模板集中管理，易于查找和修改
- ✅ 样式常量集中定义
- ✅ 代码结构更清晰

### 3. **可扩展性**
- ✅ 支持主题切换（修改 ColorScheme）
- ✅ 支持自定义配置（注入 RenderConfig）
- ✅ 易于添加新的节点类型或样式

### 4. **可测试性**
- ✅ 模板可独立测试
- ✅ 样式配置可单独验证
- ✅ 渲染逻辑更清晰

## 向后兼容性

✅ **完全兼容**: Renderer 类的公共接口保持不变：
- `__init__()` 参数未变（新增可选的 `config` 参数）
- `render_dot()` 方法签名未变
- 所有渲染方法保持原有行为

## 使用示例

### 基础使用（无变化）
```python
from fastapi_voyager.render import Renderer

renderer = Renderer(
    show_fields='all',
    module_color={'myapp.services': 'tomato'}
)
dot_output = renderer.render_dot(tags, routes, nodes, links)
```

### 高级使用（新功能）
```python
from fastapi_voyager.render import Renderer
from fastapi_voyager.render_style import RenderConfig, ColorScheme, GraphvizStyle

# 自定义颜色主题
custom_colors = ColorScheme(
    primary='#ff6b6b',
    highlight='#ffd93d'
)

# 自定义样式
custom_style = GraphvizStyle(
    font='Arial',
    node_fontsize='14'
)

# 使用自定义配置
config = RenderConfig(colors=custom_colors, style=custom_style)

renderer = Renderer(config=config)
dot_output = renderer.render_dot(tags, routes, nodes, links)
```

## 测试验证

✅ 所有现有测试通过 (18/18)
✅ 模板渲染正确
✅ 向后兼容性验证通过
✅ 实际应用场景测试通过

## 未来改进建议

1. **模板继承**: 使用 Jinja2 模板继承减少重复
2. **主题系统**: 预定义多个主题（深色、浅色、高对比度）
3. **自定义模板**: 支持用户覆盖默认模板
4. **模板验证**: 添加模板语法检查
5. **性能优化**: 缓存编译后的模板

## 迁移指南

### 对于项目维护者

无需修改现有代码，但可选地：

1. **自定义样式**:
   ```python
   from fastapi_voyager.render_style import RenderConfig, ColorScheme

   config = RenderConfig(
       colors=ColorScheme(primary='#custom-color')
   )
   renderer = Renderer(config=config)
   ```

2. **修改模板**:
   编辑 `templates/dot/*.j2` 或 `templates/html/*.j2` 文件

3. **添加新样式**:
   在 `render_style.py` 中扩展配置类

## 技术细节

### Jinja2 环境配置
```python
Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(),
    trim_blocks=True,      # 移除尾随换行符
    lstrip_blocks=True     # 移除前导空白
)
```

### 模板路径解析
```python
TEMPLATE_DIR = Path(__file__).parent / "templates"
```
自动定位到 `src/fastapi_voyager/templates/`

## 常见问题

**Q: 为什么要引入 Jinja2？**
A: 将视图模板从业务逻辑中分离，提高代码的可维护性和可扩展性。

**Q: 会影响性能吗？**
A: Jinja2 会编译并缓存模板，性能影响可忽略不计。

**Q: 如何自定义样式？**
A: 使用 RenderConfig 注入自定义配置，或直接修改 render_style.py。

**Q: 模板语法错误如何调试？**
A: Jinja2 会提供详细的错误信息，包括行号和上下文。

## 总结

此次重构成功地将散乱的模板字符串集中管理到 Jinja2 模板文件中，并提取了样式配置到专门的模块。这不仅提高了代码的可维护性，也为未来的功能扩展（如主题系统、自定义模板等）奠定了基础。

✅ **任务完成**: 所有计划任务已完成，测试通过，代码已准备就绪。
