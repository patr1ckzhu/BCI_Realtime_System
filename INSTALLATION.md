# BCI系统环境安装指南

## 在新电脑上安装（只有Miniconda）

### 步骤1：创建新的conda环境
```bash
# 创建Python 3.11环境（推荐）
conda create -n bci python=3.11 -y

# 激活环境
conda activate bci
```

### 步骤2：安装所有依赖
```bash
# 使用requirements.txt安装所有库
pip install -r requirements.txt
```

### 步骤3：验证安装
```bash
# 测试MNE
python -c "import mne; print(f'MNE version: {mne.__version__}')"

# 测试pyxdf
python -c "import pyxdf; print('pyxdf OK')"

# 测试pylsl
python -c "import pylsl; print(f'pylsl version: {pylsl.__version__}')"

# 测试psychopy
python -c "import psychopy; print(f'psychopy version: {psychopy.__version__}')"
```

---

## 核心库说明

### 数据分析和可视化工具
| 库 | 版本 | 用途 |
|---|---|---|
| **numpy** | 2.2.6 | 数值计算 |
| **scipy** | 1.14.1 | 科学计算（信号处理） |
| **pandas** | 2.3.3 | 数据分析 |
| **matplotlib** | 3.10.7 | 静态图表绘制 |
| **pyqtgraph** | 0.14.0 | 实时数据可视化 |

### EEG专用库
| 库 | 版本 | 用途 |
|---|---|---|
| **mne** | 1.11.0 | EEG/MEG数据处理和分析 |
| **pylsl** | 1.17.6 | Lab Streaming Layer实时数据流 |
| **pyxdf** | 1.17.0 | XDF文件读取 |

### 实验和GUI
| 库 | 版本 | 用途 |
|---|---|---|
| **psychopy** | 2025.2.1 | 心理学/BCI实验刺激呈现 |
| **PyQt6** | 6.10.0 | GUI框架 |

---

## 各脚本使用的库

### 数据可视化脚本
- `visualize_eeg_universal.py`: mne, numpy, matplotlib, pyxdf
- `visualize_xdf_with_mne.py`: mne, pyxdf, numpy, matplotlib
- `visualize_xdf_8ch_psd.py`: mne, pyxdf, numpy, matplotlib
- `check_xdf_alignment.py`: pyxdf, numpy, matplotlib

### 数据分析脚本
- `extract_psd.py`: mne, numpy, pandas, scipy
- `analyze_events.py`: mne, numpy
- `visualize_left_vs_right.py`: mne, numpy, matplotlib, scipy
- `visualize_erd_improved.py`: mne, numpy, matplotlib, scipy

### 实验运行脚本
- `motor_imagery_experiment.py`: psychopy, pylsl
- `bci_demo_ui.py`: PyQt6, pyqtgraph, pylsl, scipy, numpy

---

## 可能遇到的问题

### 问题1：psychopy依赖很多
如果你不需要运行实验（`motor_imagery_experiment.py`），可以跳过psychopy安装：
```bash
# 只安装数据分析所需的库
pip install numpy scipy pandas matplotlib mne pyxdf pylsl
```

### 问题2：PyQt6安装问题
如果不需要GUI（`bci_demo_ui.py`），可以跳过PyQt6和pyqtgraph：
```bash
# 最小化安装（只用于数据分析和可视化）
pip install numpy scipy pandas matplotlib mne pyxdf
```

### 问题3：conda vs pip
某些库在conda-forge中也有，可以选择用conda安装：
```bash
# 使用conda安装（可选）
conda install -c conda-forge numpy scipy pandas matplotlib mne
pip install pyxdf pylsl psychopy PyQt6 pyqtgraph
```

---

## 最小化安装（只需要数据分析）

如果只需要分析XDF/GDF/EDF数据和可视化：
```bash
# 最小依赖
pip install numpy matplotlib mne pyxdf
```

这足以运行：
- `visualize_eeg_universal.py`
- `visualize_xdf_with_mne.py`
- `visualize_xdf_8ch_psd.py`
- `check_xdf_alignment.py`

---

## 快速测试环境是否正常

创建测试脚本 `test_environment.py`：
```python
#!/usr/bin/env python3
print("Testing Python environment for BCI system...")

try:
    import numpy
    print(f"✓ numpy {numpy.__version__}")
except:
    print("✗ numpy not found")

try:
    import scipy
    print(f"✓ scipy {scipy.__version__}")
except:
    print("✗ scipy not found")

try:
    import pandas
    print(f"✓ pandas {pandas.__version__}")
except:
    print("✗ pandas not found")

try:
    import matplotlib
    print(f"✓ matplotlib {matplotlib.__version__}")
except:
    print("✗ matplotlib not found")

try:
    import mne
    print(f"✓ mne {mne.__version__}")
except:
    print("✗ mne not found")

try:
    import pyxdf
    print(f"✓ pyxdf OK")
except:
    print("✗ pyxdf not found")

try:
    import pylsl
    print(f"✓ pylsl {pylsl.__version__}")
except:
    print("✗ pylsl not found")

try:
    import psychopy
    print(f"✓ psychopy {psychopy.__version__}")
except:
    print("✗ psychopy not found (optional)")

try:
    import PyQt6
    print(f"✓ PyQt6 OK")
except:
    print("✗ PyQt6 not found (optional)")

print("\nEnvironment check complete!")
```

运行测试：
```bash
python test_environment.py
```
