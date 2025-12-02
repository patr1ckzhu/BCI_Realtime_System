"""
BCI Competition IV Data Set 2b - Motor Imagery Experiment
运动想象实验刺激呈现脚本

实验范式参考: BCI Competition IV-2b (Graz Dataset)
只实现核心的 Motor Imagery Screening 流程
"""

import random
import time
import numpy as np

# 必须在导入 psychopy.sound 之前设置音频后端
from psychopy import prefs
prefs.hardware['audioLib'] = ['pygame']

from psychopy import visual, core, event, sound
from pylsl import StreamInfo, StreamOutlet


# ============================================================================
# LSL Marker 定义 (参考 BCI IV-2b 文档)
# ============================================================================
MARKER_TRIAL_START = 768  # Trial 开始 (Fixation cross + Beep)
MARKER_LEFT_HAND = 769    # 左手运动想象提示
MARKER_RIGHT_HAND = 770   # 右手运动想象提示


# ============================================================================
# 实验参数配置 (参考 BCI IV-2b Figure 3a)
# ============================================================================
TRIALS_PER_RUN = 20       # 每个 Run 包含 20 个 Trial
TRIALS_PER_CLASS = 10     # 每类 10 个 Trial (左手/右手各10个)

# 时序参数 (单位: 秒)
TIME_FIXATION = 3.0       # 0-3s: 十字光标显示时间
TIME_CUE_DURATION = 1.25  # 3-4.25s: 提示箭头显示时长
TIME_IMAGERY = 3.75       # 4.25-8s: 运动想象持续时间 (8 - 4.25 = 3.75)
TIME_REST_BASE = 1.5      # 休息基础时间
TIME_REST_RANDOM = 1.0    # 休息随机增量 (0-1s)

# 提示音参数 (参考原文档: 1kHz, 70ms)
BEEP_FREQUENCY = 1000     # Hz
BEEP_DURATION = 0.07      # 秒

# 视觉参数
FIXATION_SIZE = 0.5       # 十字光标大小
ARROW_SIZE = 2.0          # 箭头大小
BACKGROUND_COLOR = 'black'
FOREGROUND_COLOR = 'white'


class MotorImageryExperiment:
    """运动想象实验类"""

    def __init__(self):
        """初始化实验环境"""

        print("[INFO] 正在初始化实验环境...")

        # === 1. 创建 PsychoPy 窗口 ===
        print("[INFO] 创建显示窗口...")

        self.win = visual.Window(
            size=[1600, 1000],  # 大窗口（可手动最大化）
            fullscr=False,      # 窗口模式
            color=BACKGROUND_COLOR,
            units='height',
            allowGUI=True
        )
        print("[INFO] 窗口创建成功（窗口模式）")
        print("[INFO] 提示：可将窗口拖到外接显示器，然后点击窗口左上角绿色按钮全屏")

        # === 2. 创建视觉刺激 ===
        print("[INFO] 创建视觉刺激...")
        # 十字光标 (Fixation Cross)
        self.fixation = visual.TextStim(
            self.win,
            text='+',
            height=FIXATION_SIZE,
            color=FOREGROUND_COLOR
        )

        # 左箭头提示 (Left Hand Cue)
        self.cue_left = visual.TextStim(
            self.win,
            text='<',
            height=ARROW_SIZE,
            color=FOREGROUND_COLOR,
            bold=True
        )

        # 右箭头提示 (Right Hand Cue)
        self.cue_right = visual.TextStim(
            self.win,
            text='>',
            height=ARROW_SIZE,
            color=FOREGROUND_COLOR,
            bold=True
        )

        # 空白屏幕 (使用一个不可见的刺激)
        self.blank = visual.TextStim(
            self.win,
            text='',
            color=BACKGROUND_COLOR
        )
        print("[INFO] 视觉刺激创建完成")

        # === 3. 创建听觉刺激 ===
        # 提示音 (1kHz Beep, 70ms)
        print("[INFO] 创建提示音...")
        try:
            # 方案1: 尝试使用 pygame 生成正弦波
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

            # 生成 1kHz 正弦波
            sample_rate = 22050
            duration = BEEP_DURATION
            frequency = BEEP_FREQUENCY

            import numpy as np
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t)

            # 应用汉宁窗（平滑开始和结束，避免爆音）
            window = np.hanning(len(wave))
            wave = wave * window

            # 转换为 pygame 可用的格式
            wave = (wave * 32767).astype(np.int16)
            stereo_wave = np.repeat(wave.reshape(-1, 1), 2, axis=1)

            self.beep = pygame.sndarray.make_sound(stereo_wave)
            print("[INFO] 提示音创建成功 (pygame)")

        except Exception as e:
            print(f"[WARNING] pygame 提示音创建失败: {e}")
            try:
                # 方案2: 使用系统铃声作为替代
                import os
                import platform
                if platform.system() == 'Darwin':  # macOS
                    self.beep = lambda: os.system('afplay /System/Library/Sounds/Ping.aiff &')
                    print("[INFO] 将使用系统铃声作为提示音")
                else:
                    print("[WARNING] 系统不支持，将不播放提示音")
                    self.beep = None
            except:
                print("[INFO] 将不播放提示音")
                self.beep = None

        # === 4. 初始化 LSL Marker Stream ===
        info = StreamInfo(
            name='PsychopyMarkers',
            type='Markers',
            channel_count=1,
            nominal_srate=0,  # Irregular rate
            channel_format='int32',
            source_id='psychopy_mi_experiment'
        )
        self.outlet = StreamOutlet(info)

        print("[INFO] LSL Stream 'PsychopyMarkers' 已创建")
        print(f"[INFO] 实验参数: {TRIALS_PER_RUN} Trials/Run, 左右手各 {TRIALS_PER_CLASS} 个")

    def send_marker(self, marker):
        """发送 LSL Marker"""
        self.outlet.push_sample([marker])
        print(f"[MARKER] {marker} 已发送 (时间戳: {time.time():.3f})")

    def run_trial(self, trial_type):
        """
        运行单次 Trial

        参数:
            trial_type: 'left' 或 'right'
        """

        # === t = 0s: 十字光标 + 提示音 + Marker 768 ===
        # (参考 BCI IV-2b Figure 3a)
        self.fixation.draw()
        self.win.flip()
        if self.beep is not None:
            # 播放提示音（支持 pygame.Sound 或系统铃声）
            if callable(self.beep):
                self.beep()  # 系统铃声（lambda 函数）
            else:
                self.beep.play()  # pygame Sound 对象
        self.send_marker(MARKER_TRIAL_START)

        # 等待 3 秒
        core.wait(TIME_FIXATION)

        # 检查是否按下 ESC 退出
        if 'escape' in event.getKeys():
            self.cleanup()
            core.quit()

        # === t = 3s: 显示提示箭头 (Cue) ===
        # 根据 Trial 类型显示左箭头 (<) 或右箭头 (>)
        if trial_type == 'left':
            self.cue_left.draw()
            self.win.flip()
            self.send_marker(MARKER_LEFT_HAND)
        else:  # right
            self.cue_right.draw()
            self.win.flip()
            self.send_marker(MARKER_RIGHT_HAND)

        # 提示显示 1.25 秒
        core.wait(TIME_CUE_DURATION)

        # === t = 4.25s ~ 8s: 运动想象阶段 ===
        # 提示消失，保留十字光标，受试者进行运动想象
        self.fixation.draw()
        self.win.flip()
        core.wait(TIME_IMAGERY)

        # === t = 8s: 空白屏幕 + 休息 ===
        # 屏幕变黑
        self.blank.draw()
        self.win.flip()

        # 随机休息时间: 1.5s + random(0, 1.0)s
        rest_time = TIME_REST_BASE + random.random() * TIME_REST_RANDOM
        core.wait(rest_time)

        # 检查退出
        if 'escape' in event.getKeys():
            self.cleanup()
            core.quit()

    def run_experiment(self):
        """
        运行一个完整的实验 Run (20 Trials)
        """

        # === 1. 生成 Trial 序列 (10个左手 + 10个右手，随机打乱) ===
        trial_sequence = (
            ['left'] * TRIALS_PER_CLASS +
            ['right'] * TRIALS_PER_CLASS
        )
        random.shuffle(trial_sequence)

        print(f"\n[INFO] Trial 序列已生成: {trial_sequence}")
        print(f"[INFO] 按 'Escape' 可随时退出实验\n")

        # === 2. 显示准备界面 ===
        ready_text = visual.TextStim(
            self.win,
            text='运动想象实验\n\n准备开始...\n\n按任意键开始',
            height=0.08,
            color=FOREGROUND_COLOR
        )
        ready_text.draw()
        self.win.flip()
        event.waitKeys()  # 等待按键

        # === 3. 开始倒计时 ===
        for i in range(3, 0, -1):
            countdown = visual.TextStim(
                self.win,
                text=str(i),
                height=0.2,
                color=FOREGROUND_COLOR
            )
            countdown.draw()
            self.win.flip()
            core.wait(1.0)

        # === 4. 执行所有 Trials ===
        for trial_idx, trial_type in enumerate(trial_sequence, start=1):
            print(f"\n{'='*60}")
            print(f"[Trial {trial_idx}/{TRIALS_PER_RUN}] 类型: {trial_type.upper()}")
            print(f"{'='*60}")

            self.run_trial(trial_type)

        # === 5. 实验结束 ===
        end_text = visual.TextStim(
            self.win,
            text='实验完成！\n\n感谢您的参与\n\n按任意键退出',
            height=0.08,
            color=FOREGROUND_COLOR
        )
        end_text.draw()
        self.win.flip()
        event.waitKeys()

        print("\n[INFO] 实验已完成")

    def cleanup(self):
        """清理资源"""
        print("\n[INFO] 正在清理资源...")
        self.win.close()


def main():
    """主函数"""
    exp = None
    try:
        # 创建实验对象
        print("\n[INFO] 开始初始化实验...")
        exp = MotorImageryExperiment()
        print("[INFO] 实验对象创建成功\n")

        # 运行实验
        exp.run_experiment()

        # 清理
        exp.cleanup()

    except KeyboardInterrupt:
        print("\n[INFO] 实验被用户中断")
        if exp is not None:
            exp.cleanup()

    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        if exp is not None:
            exp.cleanup()

    finally:
        core.quit()


if __name__ == "__main__":
    main()
