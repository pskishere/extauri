# Excalidraw MCP 绘制指南

本指南展示如何使用优化后的 MCP 工具进行精准的 Excalidraw 绘制。

## 可用工具

### 1. update_canvas - 更新整个画布

用于创建或更新多个元素。支持完整的 Excalidraw 元素结构。

#### 元素类型
- `rectangle` - 矩形
- `ellipse` - 椭圆
- `diamond` - 菱形
- `arrow` - 箭头
- `line` - 直线
- `freedraw` - 自由绘制
- `text` - 文本
- `image` - 图片

#### 基本属性
- `id` (必填): 唯一标识符，建议使用 UUID
- `type` (必填): 元素类型
- `x`, `y` (必填): 左上角坐标
- `width`, `height` (必填): 尺寸
- `angle`: 旋转角度（弧度）

#### 样式属性
- `strokeColor`: 边框颜色（如 '#FF0000'）
- `backgroundColor`: 填充颜色（如 '#00FF00' 或 'transparent'）
- `fillStyle`: 填充样式（'hachure', 'cross-hatch', 'solid'）
- `strokeWidth`: 边框宽度
- `strokeStyle`: 边框样式（'solid', 'dashed', 'dotted'）
- `roughness`: 粗糙度（0-3）
- `opacity`: 透明度（0-100）

#### 文本属性（仅text类型）
- `text`: 文本内容
- `fontSize`: 字体大小
- `fontFamily`: 字体族（1=Virgil, 2=Helvetica, 3=Cascadia）
- `textAlign`: 水平对齐（'left', 'center', 'right'）
- `verticalAlign`: 垂直对齐（'top', 'middle', 'bottom'）

#### 路径属性（line, arrow, freedraw类型）
- `points`: 路径点数组，格式为 [[x1,y1], [x2,y2], ...]

### 2. update_element - 更新单个元素

用于修改已存在元素的属性。支持所有上述属性。

### 3. remove_element - 删除元素

根据元素ID删除指定元素。

### 4. clear_canvas - 清空画布

删除画布上的所有元素。

### 5. export_canvas - 导出画布

将画布导出为图片格式。

## 绘制示例

### 创建一个红色矩形

```json
{
  "elements": [
    {
      "id": "rect-001",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 150,
      "strokeColor": "#FF0000",
      "backgroundColor": "transparent",
      "fillStyle": "hachure",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100
    }
  ]
}
```

### 创建带文本的元素

```json
{
  "elements": [
    {
      "id": "text-001",
      "type": "text",
      "x": 150,
      "y": 200,
      "width": 100,
      "height": 25,
      "text": "Hello World",
      "fontSize": 20,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#000000"
    }
  ]
}
```

### 创建箭头

```json
{
  "elements": [
    {
      "id": "arrow-001",
      "type": "arrow",
      "x": 50,
      "y": 50,
      "width": 200,
      "height": 100,
      "points": [[0, 0], [200, 100]],
      "strokeColor": "#0000FF",
      "strokeWidth": 3,
      "strokeStyle": "solid"
    }
  ]
}
```

## 最佳实践

1. **使用唯一ID**: 每个元素都应该有唯一的ID，建议使用描述性前缀
2. **合理设置坐标**: 确保元素在画布可见区域内
3. **选择合适的样式**: 根据需要选择填充样式和边框样式
4. **文本元素**: 确保width和height足够容纳文本内容
5. **路径元素**: points数组的坐标是相对于元素x,y的偏移量

## 颜色参考

常用颜色代码：
- 红色: `#FF0000`
- 绿色: `#00FF00`
- 蓝色: `#0000FF`
- 黑色: `#000000`
- 白色: `#FFFFFF`
- 透明: `transparent`

通过这些详细的参数定义，模型现在可以更精准地创建和操作 Excalidraw 元素。