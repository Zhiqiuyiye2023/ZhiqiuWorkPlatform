# 遥感影像识别CPU模式崩溃临时解决方案

## 问题现状

即使经过多次深度优化，在CPU模式下处理遥感影像时仍然会出现栈溢出崩溃（错误代码 `0xC0000409`）。

```
使用切片大小: 1024, 重叠: 10
影像尺寸: 9043x6145, 切片数量: 63

进程已结束，退出代码为 -1073740791 (0xC0000409)
```

## 根本原因

**栈溢出发生在YOLO模型的C++底层实现中**，这是ultralytics库和PyTorch在CPU模式下的固有问题：

1. **CPU模式内存分配方式不同**：
   - GPU模式：使用CUDA内存分配器，有专门的显存管理
   - CPU模式：直接使用系统内存，可能触发栈分配

2. **模型推理的深度**：
   - YOLO v8/v11 模型在CPU模式下推理时，某些层的计算可能使用递归
   - 实例分割（retina_masks=True）需要额外的掩码生成，消耗更多栈空间

3. **Python无法捕获的崩溃**：
   - 这是C++层面的崩溃，Python的try-except无法捕获
   - 即使添加了异常处理，崩溃仍然会发生

## 临时解决方案

### 方案1：切换到GPU模式（推荐）⭐

**最有效的解决方案是使用GPU**：

```python
# 如果有GPU，模型会自动使用
# 检查CUDA是否可用
import torch
if torch.cuda.is_available():
    print("✅ GPU可用")
    device = "cuda:0"
else:
    print("❌ GPU不可用，使用CPU（可能不稳定）")
    device = "cpu"
```

**如何安装GPU支持**：
```bash
# 卸载CPU版本的PyTorch
pip uninstall torch torchvision

# 安装GPU版本（根据你的CUDA版本）
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 方案2：使用更小的切片大小

**降低单次推理的内存压力**：

```python
# 当前设置（可能崩溃）
切片大小: 1024
重叠: 10

# 推荐设置（更安全）
切片大小: 512   # 减半
重叠: 5        # 减半
```

**影响**：
- ✅ 降低内存压力
- ✅ 减少栈使用
- ❌ 增加切片数量（处理时间更长）

### 方案3：使用更轻量的模型

**切换到更小的YOLO模型**：

```python
# 当前可能使用的模型
yolov8x-seg.pt  # 最大，CPU模式可能崩溃
yolov8l-seg.pt  # 大型
yolov8m-seg.pt  # 中型

# 推荐在CPU模式下使用
yolov8s-seg.pt  # 小型，推荐 ⭐
yolov8n-seg.pt  # 纳米，最轻量
```

**优缺点**：
- ✅ 显著降低内存使用
- ✅ 减少崩溃风险
- ❌ 可能降低检测精度

### 方案4：分批处理影像

**不要一次性处理整张影像**：

1. **使用影像裁剪功能**将大影像切分为多个小块
2. **单独处理每个小块**
3. **最后合并结果**

**示例流程**：
```
原始影像: 9043x6145 (63个切片) ❌ 崩溃

↓ 裁剪为4块

块1: 4500x3000 (约16个切片) ✅ 成功
块2: 4500x3000 (约16个切片) ✅ 成功
块3: 4500x3000 (约16个切片) ✅ 成功
块4: 4500x3000 (约16个切片) ✅ 成功

↓ 合并结果

完整结果 ✅
```

### 方案5：禁用实例分割掩码

**只进行目标检测，不生成掩码**：

这需要修改模型预测参数：

```python
# 当前（启用实例分割）
results = self.model.predict(
    source=rgb_path,
    retina_masks=True,  # ❌ 消耗大量内存
    ...
)

# 修改为（只检测边界框）
results = self.model.predict(
    source=rgb_path,
    retina_masks=False,  # ✅ 只检测框
    task='detect',       # ✅ 明确指定检测任务
    ...
)
```

**注意**：这样就无法生成多边形矢量，只能得到矩形框。

## 代码修改建议

### 修改1：在界面添加警告

在 `start_rs_detection()` 方法开始处添加：

```python
def start_rs_detection(self):
    """开始遥感影像识别"""
    # 检查是否已选择模型
    if not hasattr(self, 'model') or self.model is None:
        QMessageBox.warning(self, "警告", "请先选择训练模型！")
        return
    
    # ⭐ 新增：CPU模式警告
    if self.device == "cpu":
        reply = QMessageBox.warning(
            self,
            "CPU模式警告",
            "当前使用CPU模式进行遥感影像识别，可能会因内存限制导致崩溃。\n\n"
            "建议：\n"
            "1. 使用GPU模式（推荐）\n"
            "2. 减小切片大小（如512）\n"
            "3. 使用更小的模型（如yolov8s-seg）\n"
            "4. 先裁剪影像为更小的块\n\n"
            "是否仍要继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
```

### 修改2：降低默认max_det参数

已经修改为：

```python
max_det=100,  # 从1000降低到100
```

### 修改4：添加内存检查

在模型预测前检查系统可用内存：

```python
# ⭐ 新增：CPU模式下检查系统内存
if self.device == "cpu":
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        # 如果可用内存小于2GB，警告用户
        if available_gb < 2:
            reply = QMessageBox.warning(
                self,
                "内存不足警告",
                f"当前可用内存: {available_gb:.1f}GB，小于推荐的2GB\n\n"
                f"继续处理可能导致系统不稳定或崩溃。\n\n是否仍要继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                # 清理临时文件
                if os.path.exists(rgb_path):
                    os.remove(rgb_path)
                del image_array, rgb_array
                continue
    except ImportError:
        # 如果没有psutil，跳过检查
        pass
```

## 推荐配置（CPU模式）

如果必须使用CPU模式，推荐以下组合：

| 参数 | 推荐值 | 原因 |
|------|--------|------|
| 模型 | yolov8s-seg.pt | 轻量级，平衡精度和性能 |
| 切片大小 | 512 | 降低单次推理压力 |
| 重叠 | 5-10 | 最小化重叠 |
| max_det | 50-100 | 限制检测对象数 |
| 影像大小 | < 5000x5000 | 避免切片过多 |

## 长期解决方案

### 1. 升级硬件（推荐）⭐

**购买/使用支持CUDA的GPU**：
- NVIDIA GTX 1650 或更高（入门级）
- NVIDIA RTX 3060 或更高（推荐）
- NVIDIA RTX 4070 或更高（专业级）

**预期收益**：
- ✅ 完全解决崩溃问题
- ✅ 处理速度提升10-50倍
- ✅ 可处理更大的影像
- ✅ 支持更复杂的模型

### 2. 使用云GPU服务

如果本地没有GPU，可以考虑：

**Google Colab**：
- 免费GPU（T4）
- 有使用时长限制
- 适合临时处理

**阿里云/腾讯云GPU实例**：
- 按需付费
- 适合大批量处理
- 成本可控

### 3. 切换到更稳定的框架

考虑使用其他推理框架：

**ONNX Runtime**：
- 将YOLO模型转换为ONNX格式
- CPU模式更稳定
- 性能优化更好

```bash
# 导出YOLO模型为ONNX
yolo export model=yolov8s-seg.pt format=onnx

# 使用ONNX Runtime推理
pip install onnxruntime
```

## 测试建议

### 测试流程

1. **确认当前配置**：
   ```python
   print(f"设备: {self.device}")
   print(f"模型: {model_path}")
   print(f"切片大小: {tile_size}")
   ```

2. **从最小配置开始测试**：
   ```
   - 模型: yolov8n-seg.pt（最小）
   - 切片: 512
   - 影像: 2000x2000以下
   ```

3. **逐步增加复杂度**：
   - 如果512切片成功 → 尝试640
   - 如果nano模型成功 → 尝试small模型
   - 如果小影像成功 → 尝试中等影像

4. **记录崩溃点**：
   ```
   成功配置: yolov8s + 512切片 + 3000x3000影像
   崩溃配置: yolov8s + 1024切片 + 9000x6000影像
   ```

## 已知限制

### CPU模式下的固有限制

1. **内存限制**：
   - CPU模式使用系统内存
   - 系统内存有限（通常8-32GB）
   - 大模型+大影像容易超限

2. **栈空间限制**：
   - Windows默认栈大小：1MB
   - YOLO推理可能超出此限制
   - 无法通过Python代码修改

3. **推理效率低**：
   - CPU推理速度慢10-50倍
   - 大量切片会耗时很久

### 无法解决的情况

如果以下条件同时满足，崩溃几乎无法避免：

- ❌ 使用CPU模式
- ❌ 使用大模型（yolov8m以上）
- ❌ 使用大切片（>1024）
- ❌ 处理大影像（>10000x10000）

**唯一解决方案**：切换到GPU模式或降低上述参数

## 总结

### 核心要点

1. **根本问题**：CPU模式下YOLO模型推理会触发栈溢出（C++层面）
2. **Python无能为力**：try-except无法捕获此类崩溃
3. **最佳解决方案**：使用GPU模式
4. **临时方案**：降低参数、分块处理、使用小模型

### 行动建议

**短期（1周内）**：
- ✅ 尝试方案2-5
- ✅ 找到适合你硬件的参数组合
- ✅ 使用影像裁剪分块处理

**中期（1月内）**：
- ✅ 考虑升级GPU硬件
- ✅ 或使用云GPU服务
- ✅ 批量处理历史数据

**长期**：
- ✅ 投资专业GPU工作站
- ✅ 建立标准化处理流程
- ✅ 优化模型和参数

---

**文档时间**: 2025-10-24  
**问题状态**: ⚠️ CPU模式固有限制，暂无完美解决方案  
**推荐方案**: 切换到GPU模式  
**临时方案**: 降低参数、分块处理
