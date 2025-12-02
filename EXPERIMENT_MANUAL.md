# BCI 运动想象实验系统 - 使用手册

## 📋 目录
- [系统概述](#系统概述)
- [环境配置](#环境配置)
- [运行实验](#运行实验)
- [实验流程说明](#实验流程说明)
- [LSL Marker 说明](#lsl-marker-说明)
- [参数配置](#参数配置)
- [故障排除](#故障排除)
- [与真实系统集成](#与真实系统集成)

---

## 系统概述

### 实验范式
- **参考标准**: BCI Competition IV Data Set 2b (Graz Dataset)
- **任务类型**: 运动想象 (Motor Imagery)
- **分类目标**: 左手 vs. 右手
- **实验设计**: 每个 Run 包含 20 个 Trial（左手10个，右手10个，随机顺序）

### 文件说明
```
BCI_Realtime_System/
├── motor_imagery_experiment.py  # 实验刺激呈现脚本（本文档对应程序）
├── bci_demo_ui.py              # BCI 实时系统 UI 演示（上位机界面）
└── EXPERIMENT_MANUAL.md        # 本使用手册
```

---

## 环境配置

### 依赖库安装

```bash
# 激活 conda 环境
conda activate bci-ctnet

# 安装 Python 依赖
pip install psychopy pygame pylsl

# 安装 LSL 库（用于发送 Marker）
conda install -c conda-forge liblsl -y
```

### 验证安装

```bash
# 测试 pylsl 是否正常
python -c "from pylsl import StreamInfo, StreamOutlet; print('✓ pylsl 正常')"

# 测试 PsychoPy 是否正常
python -c "from psychopy import visual, core; print('✓ PsychoPy 正常')"
```

---

## 运行实验

### 快速启动

```bash
cd "/Users/patrick/Desktop/EEE/Fourth Year/BCI Project/BCI_Realtime_System"
python motor_imagery_experiment.py
```

### 启动流程

1. **程序初始化**（约2-3秒）
   ```
   [INFO] 开始初始化实验...
   [INFO] 正在创建显示窗口...
   [INFO] LSL Stream 'PsychopyMarkers' 已创建
   ```

2. **准备界面**
   - 屏幕显示: `运动想象实验 - 准备开始... - 按任意键开始`
   - 操作: 按**任意键**继续

3. **倒计时** (3, 2, 1)

4. **自动执行 20 个 Trial**
   - 每个 Trial 约 9.5-10.5 秒
   - 全程约 3-4 分钟

5. **实验结束**
   - 屏幕显示: `实验完成！感谢您的参与`
   - 按任意键退出

### 中途退出

**按 ESC 键** 可随时安全退出实验。

---

## 实验流程说明

### 单次 Trial 的时序设计

基于 BCI Competition IV-2b Figure 3a 标准范式：

```
┌──────────────────────────────────────────────────────────┐
│  t=0s              t=3s         t=4.25s        t=8s      │
│   │                 │              │             │        │
│   ▼                 ▼              ▼             ▼        │
│  ┌─┐               ┌─┐            ┌─┐          ┌───┐     │
│  │+│ (Fixation)    │<│ or │>│     │+│          │   │     │
│  └─┘               └─┘            └─┘          └───┘     │
│  + Beep            Cue          Imagery        Blank     │
│  (Marker 768)   (769/770)                               │
│                                                          │
│  ◄────3s────►◄─1.25s─►◄────3.75s─────►◄─1.5-2.5s─►     │
└──────────────────────────────────────────────────────────┘
```

### 阶段详解

#### 1. **Trial 开始** (t = 0s)
- **视觉**: 显示白色十字光标 `+`
- **听觉**: 播放系统提示音（70ms）
- **Marker**: 发送 **768** (Trial Start)
- **持续时间**: 3 秒

#### 2. **提示阶段** (t = 3s - 4.25s)
- **视觉**: 显示箭头
  - 左手: `<` (红色/醒目显示)
  - 右手: `>` (蓝色/醒目显示)
- **Marker**:
  - 左手: **769**
  - 右手: **770**
- **持续时间**: 1.25 秒

#### 3. **运动想象阶段** (t = 4.25s - 8s)
- **视觉**: 箭头消失，保留十字光标 `+`
- **受试者任务**: 根据刚才的提示，持续想象对应手的运动（如握拳、张开等）
- **持续时间**: 3.75 秒

#### 4. **休息阶段** (t = 8s - ?)
- **视觉**: 屏幕变黑
- **持续时间**: 1.5 - 2.5 秒（随机）

---

## LSL Marker 说明

### Marker 定义

| Marker ID | 含义 | 发送时刻 |
|-----------|------|---------|
| **768** | Trial 开始 | 十字光标出现 + Beep |
| **769** | 左手运动想象提示 | 左箭头 `<` 出现 |
| **770** | 右手运动想象提示 | 右箭头 `>` 出现 |

### LSL Stream 信息

- **Stream 名称**: `PsychopyMarkers`
- **Stream 类型**: `Markers`
- **通道数**: 1
- **数据格式**: `int32`

### 在 EEG 采集软件中接收 Marker

#### OpenViBE
1. 添加 `LSL Import` 盒子
2. 搜索名为 `PsychopyMarkers` 的 Stream
3. 连接到 `Signal Display` 或 `GDF File Writer`

#### BrainVision Recorder
1. 启用 `LSL Marker` 接收
2. 在配置中搜索 `PsychopyMarkers`

#### Lab Recorder
1. 打开 Lab Recorder
2. 勾选 `PsychopyMarkers` Stream
3. 开始录制（自动同步时间戳）

---

## 参数配置

所有参数在 `motor_imagery_experiment.py` 文件顶部定义，可根据需要修改：

### 实验设计参数

```python
TRIALS_PER_RUN = 20       # 每个 Run 的 Trial 数量
TRIALS_PER_CLASS = 10     # 每类的 Trial 数量
```

**示例修改**: 如果想快速测试（只做4个Trial）：
```python
TRIALS_PER_RUN = 4
TRIALS_PER_CLASS = 2
```

### 时序参数

```python
TIME_FIXATION = 3.0       # 十字光标显示时间（秒）
TIME_CUE_DURATION = 1.25  # 提示箭头显示时长（秒）
TIME_IMAGERY = 3.75       # 运动想象持续时间（秒）
TIME_REST_BASE = 1.5      # 休息基础时间（秒）
TIME_REST_RANDOM = 1.0    # 休息随机增量（0-1秒）
```

**注意**: 修改时序参数会偏离 BCI IV-2b 标准范式。

### 视觉参数

```python
FIXATION_SIZE = 0.5       # 十字光标大小
ARROW_SIZE = 2.0          # 箭头大小
BACKGROUND_COLOR = 'black'
FOREGROUND_COLOR = 'white'
```

### 窗口设置

在 `__init__` 方法中修改（第58-65行）：

```python
self.win = visual.Window(
    size=[1200, 800],      # 窗口大小
    fullscr=False,         # 全屏模式: True=全屏, False=窗口
    color=BACKGROUND_COLOR,
    units='height',
    allowGUI=True
)
```

**切换到全屏模式**:
```python
fullscr=True,
size=[1920, 1080],  # 根据你的屏幕分辨率调整
```

---

## 故障排除

### 1. 窗口一闪而过

**原因**: 程序在初始化时崩溃。

**解决方法**:
```bash
python motor_imagery_experiment.py 2>&1 | tee experiment_log.txt
```
查看完整错误日志。

### 2. 提示音无法播放

**现象**: 程序显示 `[WARNING] 无法创建提示音`

**影响**: **不影响核心功能**，视觉提示仍然正常。

**可选修复** (如果你需要声音):
```bash
pip uninstall psychtoolbox -y  # 卸载有问题的库
pip install sounddevice        # 安装备用音频库
```

### 3. LSL Marker 未接收到

**检查步骤**:

1. 确认 LSL 库已安装:
```bash
python -c "from pylsl import StreamInfo; print('OK')"
```

2. 使用 LSL LabRecorder 测试:
   - 启动实验程序
   - 打开 LabRecorder
   - 查看是否出现 `PsychopyMarkers` Stream

3. 检查防火墙设置（macOS）:
```bash
# 允许 Python 通过防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
```

### 4. 字体警告

**现象**:
```
WARNING Font Manager failed to load file .../PingFangUI.ttc
```

**影响**: 仅为警告，不影响程序运行。

**消除方法** (可选):
编辑 PsychoPy 配置，指定可用字体（通常无需处理）。

---

## 与真实系统集成

### 替换数据模拟为真实 UDP 接收

当前代码中，以下位置需要替换：

#### 1. 接收真实 EEG 数据（用于 UI 演示）

**文件**: `bci_demo_ui.py`

**位置**: `DataSimulatorThread.run()` 方法（第36行）

**替换为**:
```python
def run(self):
    self.running = True

    # 创建 UDP Socket
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 8888))  # 监听 ESP32 发来的数据

    while self.running:
        data, addr = sock.recvfrom(4096)

        # 解析 ESP32 发来的数据（根据你的协议）
        # 假设格式: 8 通道 × 10 样本点 × 4 字节（float32）
        eeg_data = np.frombuffer(data, dtype=np.float32)
        eeg_data = eeg_data.reshape(8, 10)

        self.new_data.emit(eeg_data)
```

#### 2. 接入真实 CTNet 模型推理

**文件**: `bci_demo_ui.py`

**位置**: `on_new_eeg_data()` 方法后添加推理逻辑

**示例**:
```python
def on_new_eeg_data(self, data):
    # 1. 原有的数据缓冲代码...

    # 2. 添加模型推理
    if len(self.eeg_buffers[0]) >= 1000:  # 累积足够数据
        # 提取最近 4 秒数据 (250Hz × 4s = 1000 样本)
        eeg_segment = np.array([
            list(self.eeg_buffers[ch])[-1000:]
            for ch in range(8)
        ])

        # 调用 CTNet 模型
        probs = self.ctnet_model.predict(eeg_segment)
        self.new_inference.emit(probs)
```

### 集成到完整 BCI 系统的工作流程

```
┌─────────────────────────────────────────────────────────┐
│                    完整 BCI 系统流程                      │
└─────────────────────────────────────────────────────────┘

1. 启动数据采集
   └─> bci_demo_ui.py (上位机) 连接到 ESP32

2. 启动实验程序
   └─> motor_imagery_experiment.py 开始呈现刺激

3. 数据同步
   ├─> ESP32 通过 UDP 发送 EEG 数据到 PC
   └─> 实验程序通过 LSL 发送 Marker 到 PC

4. 实时处理
   ├─> 上位机接收 EEG + Marker
   ├─> CTNet 模型实时推理
   └─> 显示分类结果

5. 数据保存
   └─> 保存为 .gdf 或 .fif 格式，用于离线分析
```

---

## 快速参考卡片

### 启动命令
```bash
python motor_imagery_experiment.py
```

### 快捷键
- **任意键**: 开始实验 / 继续
- **ESC**: 退出实验

### 重要 Marker
- **768**: Trial 开始
- **769**: 左手
- **770**: 右手

### 实验时长
- 单个 Trial: ~10 秒
- 完整 Run (20 Trials): ~3-4 分钟

### 联系方式
如有问题，请查看:
- GitHub Issues: [项目仓库]
- 文档: `EXPERIMENT_MANUAL.md`

---

## 附录: BCI Competition IV-2b 参考文献

**Citation**:
```
Leeb, R., Brunner, C., Müller-Putz, G., Schlögl, A., & Pfurtscheller, G. (2008).
BCI Competition 2008 – Graz data set B.
Graz University of Technology, Austria.
```

**原始文档**: [BCI Competition IV Description](http://www.bbci.de/competition/iv/)

---

**最后更新**: 2025-11-20
**版本**: 1.0
**作者**: BCI Project Team