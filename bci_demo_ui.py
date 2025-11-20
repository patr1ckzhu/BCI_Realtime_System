"""
BCI 实时系统 UI 演示程序
基于 CTNet 模型的运动想象分类系统上位机界面
使用 PyQt6 + pyqtgraph 实现

Hardware: ADS1299 -> ESP32 (UDP) -> PC
"""

import sys
import numpy as np
from collections import deque
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg


class DataSimulatorThread(QThread):
    """数据模拟线程 - 未来替换为 UDP 接收线程"""

    # 信号：发送模拟的 EEG 数据和推理结果
    new_data = pyqtSignal(np.ndarray)  # 8通道 EEG 数据
    new_inference = pyqtSignal(np.ndarray)  # [left_prob, right_prob]

    def __init__(self):
        super().__init__()
        self.running = False
        self.sample_rate = 250  # Hz (ADS1299 典型采样率)
        self.n_channels = 8
        self.time = 0
        self.inference_counter = 0
        self.current_class = 0  # 0=左手, 1=右手

    def run(self):
        """运行数据模拟"""
        self.running = True

        while self.running:
            # === 1. 模拟 8 通道 EEG 数据 ===
            # 生成一批数据 (每次10个样本点)
            batch_size = 10
            t = np.linspace(self.time, self.time + batch_size/self.sample_rate, batch_size)

            # 为每个通道生成不同频率的正弦波 + 噪声
            eeg_data = np.zeros((self.n_channels, batch_size))
            for ch in range(self.n_channels):
                # 主频率在 8-13 Hz (Alpha波段) 和 13-30 Hz (Beta波段)
                freq1 = 10 + ch * 0.5  # Alpha
                freq2 = 20 + ch * 1.0  # Beta

                signal = (np.sin(2 * np.pi * freq1 * t) * 20 +
                         np.sin(2 * np.pi * freq2 * t) * 10 +
                         np.random.randn(batch_size) * 5)  # 噪声

                eeg_data[ch, :] = signal

            self.new_data.emit(eeg_data)
            self.time += batch_size / self.sample_rate

            # === 2. 模拟推理结果 ===
            # 每隔一段时间切换左右手
            self.inference_counter += 1
            if self.inference_counter % 150 == 0:  # 约每3秒切换
                self.current_class = 1 - self.current_class

            # 生成概率值（带一些随机波动）
            if self.current_class == 0:  # 左手
                left_prob = 0.7 + np.random.randn() * 0.1
                right_prob = 0.3 + np.random.randn() * 0.1
            else:  # 右手
                left_prob = 0.3 + np.random.randn() * 0.1
                right_prob = 0.7 + np.random.randn() * 0.1

            # 归一化到 [0, 1] 并确保和为1
            probs = np.array([left_prob, right_prob])
            probs = np.clip(probs, 0.05, 0.95)
            probs = probs / probs.sum()

            self.new_inference.emit(probs)

            # 控制更新频率 (20ms 约等于 50 FPS)
            self.msleep(20)

    def stop(self):
        """停止线程"""
        self.running = False


class BCIMainWindow(QMainWindow):
    """BCI 系统主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCI 实时运动想象分类系统 - CTNet")
        self.setGeometry(100, 100, 1600, 900)

        # 数据缓冲区
        self.n_channels = 8
        self.buffer_size = 1000  # 显示最近1000个点
        self.eeg_buffers = [deque(maxlen=self.buffer_size) for _ in range(self.n_channels)]
        self.time_buffer = deque(maxlen=self.buffer_size)
        self.time_counter = 0

        # 频谱数据缓冲
        self.spectrogram_buffer = deque(maxlen=100)

        # 推理结果
        self.inference_probs = np.array([0.5, 0.5])

        # 数据模拟线程
        self.data_thread = None
        self.is_connected = False

        # 设置深色主题
        self.setup_dark_theme()

        # 初始化UI
        self.init_ui()

    def setup_dark_theme(self):
        """设置深色科技感主题"""
        # 设置 pyqtgraph 背景
        pg.setConfigOption('background', '#0a0e27')
        pg.setConfigOption('foreground', '#00ff88')

        # 设置应用程序样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0e27;
            }
            QWidget {
                background-color: #0a0e27;
                color: #00ff88;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QGroupBox {
                border: 2px solid #00ff88;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #1a3a52;
                border: 2px solid #00ff88;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a4a62;
            }
            QPushButton:pressed {
                background-color: #00ff88;
                color: #0a0e27;
            }
            QPushButton:disabled {
                background-color: #0f1520;
                border: 2px solid #334455;
                color: #334455;
            }
            QLineEdit {
                background-color: #1a1e2e;
                border: 2px solid #334455;
                border-radius: 3px;
                padding: 5px;
                color: #00ff88;
            }
            QLabel {
                color: #00ff88;
            }
        """)

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # === 1. 顶部：连接控制区 ===
        control_group = self.create_control_panel()
        main_layout.addWidget(control_group)

        # === 2. 中间：主显示区域 ===
        content_layout = QHBoxLayout()

        # 左侧：EEG 波形显示
        eeg_group = self.create_eeg_display()
        content_layout.addWidget(eeg_group, 3)

        # 右侧：推理结果 + 频谱
        right_layout = QVBoxLayout()

        # 推理结果
        inference_group = self.create_inference_display()
        right_layout.addWidget(inference_group, 2)

        # 频谱图
        spectrum_group = self.create_spectrum_display()
        right_layout.addWidget(spectrum_group, 1)

        content_layout.addLayout(right_layout, 2)
        main_layout.addLayout(content_layout)

        # === 3. 底部：系统状态 ===
        status_group = self.create_status_panel()
        main_layout.addWidget(status_group)

        # 设置定时器更新显示
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start(50)  # 50ms 更新一次

    def create_control_panel(self):
        """创建连接控制面板"""
        group = QGroupBox("设备连接控制")
        layout = QHBoxLayout()

        # IP地址输入
        layout.addWidget(QLabel("ESP32 IP:"))
        self.ip_input = QLineEdit("192.168.1.100")
        self.ip_input.setFixedWidth(150)
        layout.addWidget(self.ip_input)

        # 端口输入
        layout.addWidget(QLabel("端口:"))
        self.port_input = QLineEdit("8888")
        self.port_input.setFixedWidth(80)
        layout.addWidget(self.port_input)

        # 连接按钮
        self.connect_btn = QPushButton("🔌 连接设备")
        self.connect_btn.setFixedWidth(150)
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)

        layout.addStretch()

        # 连接状态指示
        self.connection_status = QLabel("● 未连接")
        self.connection_status.setStyleSheet("color: #ff4444; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.connection_status)

        group.setLayout(layout)
        return group

    def create_eeg_display(self):
        """创建 8 通道 EEG 波形显示"""
        group = QGroupBox("原始脑电信号 (8 通道)")
        layout = QVBoxLayout()

        # 创建 pyqtgraph 绘图窗口
        self.eeg_plot_widget = pg.GraphicsLayoutWidget()

        # 创建 8 个子图
        self.eeg_plots = []
        self.eeg_curves = []

        channel_names = ['Fp1', 'Fp2', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2']
        colors = ['#00ff88', '#00ffff', '#ffff00', '#ff8800',
                 '#ff00ff', '#8800ff', '#ff0088', '#88ff00']

        for i in range(self.n_channels):
            plot = self.eeg_plot_widget.addPlot(row=i, col=0)
            plot.setLabel('left', channel_names[i], color='#00ff88')
            plot.showGrid(x=True, y=True, alpha=0.3)
            plot.setYRange(-50, 50)
            plot.setMouseEnabled(x=False, y=False)

            # 隐藏除了最后一个图之外的 x 轴
            if i < self.n_channels - 1:
                plot.getAxis('bottom').setStyle(showValues=False)
            else:
                plot.setLabel('bottom', '时间 (s)', color='#00ff88')

            curve = plot.plot(pen=pg.mkPen(color=colors[i], width=1.5))
            self.eeg_plots.append(plot)
            self.eeg_curves.append(curve)

        layout.addWidget(self.eeg_plot_widget)
        group.setLayout(layout)
        return group

    def create_inference_display(self):
        """创建推理结果显示"""
        group = QGroupBox("运动想象推理结果 (CTNet)")
        layout = QVBoxLayout()

        # 类别指示器（大标题）
        self.class_indicator = QLabel("待检测")
        self.class_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.class_indicator.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #00ff88;
            background-color: #1a1e2e;
            border-radius: 10px;
            padding: 20px;
        """)
        layout.addWidget(self.class_indicator)

        # 概率柱状图
        self.prob_plot_widget = pg.PlotWidget()
        self.prob_plot_widget.setBackground('#0a0e27')
        self.prob_plot_widget.setYRange(0, 1)
        self.prob_plot_widget.setLabel('left', '概率', color='#00ff88')
        self.prob_plot_widget.setLabel('bottom', '类别', color='#00ff88')
        self.prob_plot_widget.showGrid(y=True, alpha=0.3)
        self.prob_plot_widget.setMouseEnabled(x=False, y=False)

        # 设置柱状图
        self.prob_bargraph = pg.BarGraphItem(
            x=[0, 1],
            height=[0.5, 0.5],
            width=0.6,
            brushes=[pg.mkBrush(255, 68, 68), pg.mkBrush(68, 68, 255)]
        )
        self.prob_plot_widget.addItem(self.prob_bargraph)

        # 设置 x 轴标签
        ax = self.prob_plot_widget.getAxis('bottom')
        ax.setTicks([[(0, '左手'), (1, '右手')]])

        layout.addWidget(self.prob_plot_widget)

        # 置信度文本
        self.confidence_label = QLabel("置信度: --")
        self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confidence_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.confidence_label)

        group.setLayout(layout)
        return group

    def create_spectrum_display(self):
        """创建频谱图显示"""
        group = QGroupBox("频域能量分布")
        layout = QVBoxLayout()

        self.spectrum_plot_widget = pg.PlotWidget()
        self.spectrum_plot_widget.setBackground('#0a0e27')
        self.spectrum_plot_widget.setLabel('left', '功率 (dB)', color='#00ff88')
        self.spectrum_plot_widget.setLabel('bottom', '频率 (Hz)', color='#00ff88')
        self.spectrum_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.spectrum_plot_widget.setMouseEnabled(x=False, y=False)

        # Alpha 和 Beta 波段标记
        alpha_region = pg.LinearRegionItem([8, 13], brush=(255, 255, 0, 30))
        beta_region = pg.LinearRegionItem([13, 30], brush=(0, 255, 255, 30))
        alpha_region.setMovable(False)
        beta_region.setMovable(False)
        self.spectrum_plot_widget.addItem(alpha_region)
        self.spectrum_plot_widget.addItem(beta_region)

        self.spectrum_curve = self.spectrum_plot_widget.plot(
            pen=pg.mkPen(color='#00ff88', width=2)
        )

        layout.addWidget(self.spectrum_plot_widget)
        group.setLayout(layout)
        return group

    def create_status_panel(self):
        """创建系统状态面板"""
        group = QGroupBox("系统状态")
        layout = QHBoxLayout()

        self.fps_label = QLabel("FPS: --")
        self.samples_label = QLabel("采样率: -- Hz")
        self.packets_label = QLabel("数据包: 0")
        self.model_label = QLabel("模型: CTNet (未加载)")

        for label in [self.fps_label, self.samples_label,
                     self.packets_label, self.model_label]:
            label.setStyleSheet("font-size: 12px;")
            layout.addWidget(label)
            layout.addWidget(self.create_separator())

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_separator(self):
        """创建分隔符"""
        separator = QLabel("|")
        separator.setStyleSheet("color: #334455;")
        return separator

    def toggle_connection(self):
        """切换连接状态"""
        if not self.is_connected:
            # 开始连接
            self.connect_btn.setText("⚡ 已连接")
            self.connect_btn.setEnabled(False)
            self.connection_status.setText("● 已连接")
            self.connection_status.setStyleSheet(
                "color: #00ff88; font-size: 14px; font-weight: bold;"
            )
            self.model_label.setText("模型: CTNet (已加载)")

            # 启动数据模拟线程
            # TODO: 替换为真实的 UDP 接收线程
            self.data_thread = DataSimulatorThread()
            self.data_thread.new_data.connect(self.on_new_eeg_data)
            self.data_thread.new_inference.connect(self.on_new_inference)
            self.data_thread.start()

            self.is_connected = True

            # 2秒后重新启用按钮（允许断开）
            QTimer.singleShot(2000, lambda: self.connect_btn.setEnabled(True))
            QTimer.singleShot(2000, lambda: self.connect_btn.setText("🔌 断开连接"))
        else:
            # 断开连接
            if self.data_thread:
                self.data_thread.stop()
                self.data_thread.wait()

            self.connect_btn.setText("🔌 连接设备")
            self.connection_status.setText("● 未连接")
            self.connection_status.setStyleSheet(
                "color: #ff4444; font-size: 14px; font-weight: bold;"
            )
            self.model_label.setText("模型: CTNet (未加载)")
            self.is_connected = False

    def on_new_eeg_data(self, data):
        """接收新的 EEG 数据"""
        # data shape: (n_channels, batch_size)
        batch_size = data.shape[1]

        # 更新缓冲区
        for i in range(batch_size):
            self.time_buffer.append(self.time_counter)
            self.time_counter += 1/250  # 假设采样率 250 Hz

            for ch in range(self.n_channels):
                self.eeg_buffers[ch].append(data[ch, i])

        # 更新采样率显示
        self.samples_label.setText("采样率: 250 Hz")

    def on_new_inference(self, probs):
        """接收新的推理结果"""
        # TODO: 替换为真实的 CTNet 模型推理
        self.inference_probs = probs

        # 更新类别指示器
        if probs[0] > probs[1]:
            self.class_indicator.setText("← 左手")
            self.class_indicator.setStyleSheet("""
                font-size: 48px;
                font-weight: bold;
                color: #ff4444;
                background-color: #1a1e2e;
                border-radius: 10px;
                padding: 20px;
            """)
        else:
            self.class_indicator.setText("右手 →")
            self.class_indicator.setStyleSheet("""
                font-size: 48px;
                font-weight: bold;
                color: #4444ff;
                background-color: #1a1e2e;
                border-radius: 10px;
                padding: 20px;
            """)

        # 更新置信度
        confidence = max(probs) * 100
        self.confidence_label.setText(f"置信度: {confidence:.1f}%")

    def update_plots(self):
        """更新所有图表"""
        if not self.is_connected or len(self.time_buffer) == 0:
            return

        # 更新 EEG 波形
        time_array = np.array(self.time_buffer)
        for ch in range(self.n_channels):
            data_array = np.array(self.eeg_buffers[ch])
            self.eeg_curves[ch].setData(time_array, data_array)

        # 更新推理概率柱状图
        self.prob_bargraph.setOpts(
            height=self.inference_probs.tolist()
        )

        # 更新频谱图（使用第一个通道的数据）
        if len(self.eeg_buffers[0]) >= 256:
            data = np.array(list(self.eeg_buffers[0])[-256:])

            # 计算 FFT
            fft_vals = np.fft.rfft(data * np.hanning(len(data)))
            fft_freq = np.fft.rfftfreq(len(data), 1/250)
            fft_power = 20 * np.log10(np.abs(fft_vals) + 1e-10)

            # 只显示 0-50 Hz
            freq_mask = fft_freq <= 50
            self.spectrum_curve.setData(fft_freq[freq_mask], fft_power[freq_mask])

        # 更新 FPS
        self.fps_label.setText(f"FPS: {1000//50}")

        # 更新数据包计数
        packet_count = int(self.time_counter * 250 / 10)
        self.packets_label.setText(f"数据包: {packet_count}")


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序字体
    font = QFont("Consolas", 10)
    app.setFont(font)

    # 创建主窗口
    window = BCIMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
