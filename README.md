# BCI Real-time System

基于 CTNet 模型的实时脑机接口（BCI）运动想象分类系统

## 项目概述

本项目实现了一个完整的 BCI 运动想象（Motor Imagery）实时处理系统，包括：

- **实验刺激呈现**：符合 BCI Competition IV-2b 标准范式
- **实时数据采集**：ESP32 (UDP) → PC 上位机
- **在线分类**：基于 CTNet 深度学习模型
- **可视化界面**：实时显示 EEG 波形、频谱和推理结果

## 系统架构

```
┌──────────────┐  UDP   ┌──────────────┐  LSL    ┌──────────────┐
│   ADS1299    │ -----> │    ESP32     │ ------> │   上位机 PC   │
│  (EEG 采集)  │        │  (无线传输)  │         │ (数据处理)    │
└──────────────┘        └──────────────┘         └──────────────┘
                                                        │
                                                        ├─> EEG 可视化
                                                        ├─> CTNet 推理
                                                        └─> 结果显示
```

## 文件说明

| 文件 | 功能 |
|------|------|
| `motor_imagery_experiment.py` | 实验刺激呈现程序（BCI IV-2b 标准范式） |
| `bci_demo_ui.py` | 上位机可视化界面（EEG 波形 + 推理结果） |
| `EXPERIMENT_MANUAL.md` | 完整使用手册（实验流程、参数配置、故障排除） |

## 快速开始

### 环境配置

```bash
# 创建 conda 环境
conda create -n bci-ctnet python=3.10
conda activate bci-ctnet

# 安装依赖
pip install psychopy pygame pylsl pyqtgraph PyQt6 numpy
conda install -c conda-forge liblsl -y
```

### 运行实验刺激程序

```bash
python motor_imagery_experiment.py
```

**实验流程**：
1. 显示准备界面 → 按任意键开始
2. 倒计时 3, 2, 1
3. 自动执行 20 个 Trial（左手/右手各 10 个）
4. 完成后显示结束界面

### 运行上位机界面

```bash
python bci_demo_ui.py
```

**功能演示**：
- 8 通道 EEG 实时波形显示
- 左手/右手运动想象推理结果
- 频谱分析（Alpha/Beta 波段）
- 系统状态监控

## 实验范式

基于 **BCI Competition IV Data Set 2b** (Graz Dataset) 标准：

```
t=0s              t=3s         t=4.25s        t=8s
 │                 │              │             │
 ▼                 ▼              ▼             ▼
┌─┐               ┌─┐            ┌─┐          ┌───┐
│+│ (Fixation)    │<│ or │>│     │+│          │   │
└─┘               └─┘            └─┘          └───┘
+ Beep            Cue          Imagery        Blank
(Marker 768)   (769/770)

◄────3s────►◄─1.25s─►◄────3.75s─────►◄─1.5-2.5s─►
```

### LSL Marker 说明

| Marker | 含义 |
|--------|------|
| **768** | Trial 开始 (Fixation + Beep) |
| **769** | 左手运动想象提示 |
| **770** | 右手运动想象提示 |

## 配置参数

所有参数可在文件顶部修改：

```python
# 实验设计
TRIALS_PER_RUN = 20       # 每个 Run 的 Trial 数量
TRIALS_PER_CLASS = 10     # 每类的 Trial 数量

# 时序参数
TIME_FIXATION = 3.0       # 十字光标时间（秒）
TIME_CUE_DURATION = 1.25  # 提示时长（秒）
TIME_IMAGERY = 3.75       # 运动想象时间（秒）
```

详细配置请参考 [`EXPERIMENT_MANUAL.md`](EXPERIMENT_MANUAL.md)

## 与真实系统集成

### 替换数据模拟为真实 UDP 接收

**文件**: `bci_demo_ui.py` → `DataSimulatorThread.run()`

```python
# 创建 UDP Socket
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 8888))

while self.running:
    data, addr = sock.recvfrom(4096)
    eeg_data = np.frombuffer(data, dtype=np.float32)
    eeg_data = eeg_data.reshape(8, 10)
    self.new_data.emit(eeg_data)
```

### 集成 CTNet 模型推理

```python
# 加载训练好的模型
self.ctnet_model = torch.load('ctnet_model.pth')

# 实时推理
if len(self.eeg_buffers[0]) >= 1000:
    eeg_segment = np.array([list(buf)[-1000:] for buf in self.eeg_buffers])
    probs = self.ctnet_model.predict(eeg_segment)
    self.new_inference.emit(probs)
```

## 技术栈

- **硬件**: ADS1299 (8通道 EEG 采集), ESP32 (WiFi/UDP 传输)
- **实验呈现**: PsychoPy, LSL (Lab Streaming Layer)
- **数据处理**: NumPy, SciPy
- **深度学习**: PyTorch, CTNet
- **可视化**: PyQt6, pyqtgraph

## 项目特点

- 符合国际标准 BCI IV-2b 实验范式
- 完整的 LSL Marker 同步机制
- 专业的深色科技感 UI 界面
- 模块化设计，易于扩展和集成
- 详细的中文文档和注释

## 参考文献

```
Leeb, R., Brunner, C., Müller-Putz, G., Schlögl, A., & Pfurtscheller, G. (2008).
BCI Competition 2008 – Graz data set B.
Graz University of Technology, Austria.
```

## 待办事项

- ESP32 硬件集成与 UDP 数据接收
- CTNet 模型训练与集成
- 数据保存功能（.gdf/.fif 格式）
- 在线校准与自适应算法
- 多受试者数据库管理

## 作者

BCI Project Team - EEE Fourth Year Project

## 许可证

MIT License

---

**最后更新**: 2025-11-20
