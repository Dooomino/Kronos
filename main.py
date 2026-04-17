import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from datetime import datetime, timedelta
import warnings
import akshare as ak
from typing import Dict, List, Tuple, Optional
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import logging
from logging.handlers import RotatingFileHandler

warnings.filterwarnings('ignore')

# 配置日志系统
def setup_logger(gui_app=None):
    """配置日志记录器
    
    Args:
        gui_app: GUI应用实例，用于将日志输出到窗口
    """
    # 创建 logs 目录
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger('StockPredictor')
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的 handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器（带轮转，最大10MB，保留5个备份）
    log_file = os.path.join(log_dir, f'stock_predictor_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # GUI日志处理器（如果提供了GUI应用）
    if gui_app is not None:
        gui_handler = GUILogHandler(gui_app)
        gui_handler.setLevel(logging.DEBUG)
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)
    
    return logger


class GUILogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到GUI窗口"""
    
    def __init__(self, gui_app):
        super().__init__()
        self.gui_app = gui_app
    
    def emit(self, record):
        """发送日志记录到GUI"""
        try:
            msg = self.format(record)
            # 在主线程中更新UI
            if hasattr(self.gui_app, 'log_text') and self.gui_app.show_log_var.get():
                self.gui_app.root.after(0, self._append_log, msg, record.levelno)
        except Exception:
            self.handleError(record)
    
    def _append_log(self, msg, level):
        """追加日志到文本框"""
        try:
            self.gui_app.log_text.config(state=tk.NORMAL)
            self.gui_app.log_text.insert(tk.END, msg + '\n')
            
            # 根据日志级别设置颜色标签
            if level >= logging.ERROR:
                # 错误日志：红色
                pass  # 可以添加tag配置
            elif level >= logging.WARNING:
                # 警告日志：黄色
                pass
            
            # 自动滚动到底部
            self.gui_app.log_text.see(tk.END)
            self.gui_app.log_text.config(state=tk.DISABLED)
        except Exception:
            pass

# 初始化日志
logger = setup_logger()

# 股票名称缓存（内存缓存，程序重启后清空）
stock_name_cache = {}

# 禁止 Hugging Face Hub 自动检查和更新（适用于受限网络环境）
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'  # 禁用遥测
os.environ['HF_HUB_OFFLINE'] = '0'  # 如果完全离线设为 '1'
os.environ['TRANSFORMERS_OFFLINE'] = '0'  # 如果完全离线设为 '1'

# 添加项目路径以便导入自定义模块
sys.path.append(os.path.dirname(__file__))
try:
    from model import Kronos, KronosTokenizer, KronosPredictor
except ImportError:
    logger.warning("⚠️ 无法导入Kronos模型，预测功能将不可用")

# 导入数据源管理器
try:
    from data_sources import DataSourceManager
except ImportError:
    logger.warning("⚠️ 无法导入数据源管理器，将使用旧版数据获取方式")
    DataSourceManager = None

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class StockPredictorApp:
    """股票预测应用 - 简化版"""

    def __init__(self, root):
        self.root = root
        self.root.title("Kronos股票预测系统")
        self.root.geometry("700x800")
        self.root.configure(bg='#f0f0f0')
        
        # 重新配置logger，添加GUI处理器
        global logger
        logger = setup_logger(gui_app=self)

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(
            self.root,
            text="🤖 Kronos股票预测系统",
            font=("Arial", 16, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=10)

        # 主框架
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 输入框架
        input_frame = tk.LabelFrame(main_frame, text="参数设置", font=("Arial", 11, "bold"),
                                    bg='#f0f0f0', fg='#2c3e50', padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=10)
        
        # 配置列权重，实现对齐
        input_frame.grid_columnconfigure(1, weight=1)  # 股票代码输入框列
        input_frame.grid_columnconfigure(4, weight=1)  # 股票名称输入框列

        # 第一行：股票代码 + 状态 + 股票名称
        # 股票代码标签（右对齐）
        tk.Label(input_frame, text="股票代码:", bg='#f0f0f0', font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.E, padx=(10, 5), pady=5)
        self.stock_code_var = tk.StringVar(value="000001")
        stock_code_entry = tk.Entry(input_frame, textvariable=self.stock_code_var, font=("Arial", 10), width=12)
        stock_code_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(5, 5), pady=5)
        
        # 绑定事件：股票代码变化时自动获取名称
        self.stock_code_var.trace_add('write', self.on_stock_code_changed)
        
        # 状态标签
        self.name_status_var = tk.StringVar(value="")
        name_status_label = tk.Label(
            input_frame,
            textvariable=self.name_status_var,
            bg='#f0f0f0',
            font=("Arial", 8),
            fg='#7f8c8d',
            width=12,  # 固定宽度防止抖动
            anchor='w'  # 左对齐文本
        )
        name_status_label.grid(row=0, column=2, padx=(5, 5), pady=5, sticky=tk.W)

        # 股票名称标签（右对齐）
        tk.Label(input_frame, text="股票名称:", bg='#f0f0f0', font=("Arial", 10)).grid(
            row=0, column=3, sticky=tk.E, padx=(5, 5), pady=5)
        self.stock_name_var = tk.StringVar(value="平安银行")
        stock_name_entry = tk.Entry(input_frame, textvariable=self.stock_name_var, font=("Arial", 10), width=15, state=tk.DISABLED)
        stock_name_entry.grid(row=0, column=4, sticky=tk.W+tk.E, padx=(5, 10), pady=5)

        # 第二行：预测天数 + 历史年限
        # 预测天数标签（右对齐）
        tk.Label(input_frame, text="预测天数:", bg='#f0f0f0', font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.E, padx=(10, 5), pady=5)
        self.pred_days_var = tk.StringVar(value="60")
        pred_days_entry = tk.Entry(input_frame, textvariable=self.pred_days_var, font=("Arial", 10), width=12)
        pred_days_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(5, 5), pady=5)

        # 历史年限标签（右对齐）
        tk.Label(input_frame, text="历史年限:", bg='#f0f0f0', font=("Arial", 10)).grid(
            row=1, column=3, sticky=tk.E, padx=(5, 5), pady=5)
        self.history_years_var = tk.StringVar(value="1")
        history_years_entry = tk.Entry(input_frame, textvariable=self.history_years_var, font=("Arial", 10), width=12)
        history_years_entry.grid(row=1, column=4, sticky=tk.W+tk.E, padx=(5, 10), pady=5)

        # 第三行：使用缓存选项（居中）
        self.use_cache_var = tk.BooleanVar(value=True)
        cache_check = tk.Checkbutton(
            input_frame,
            text="✓ 使用缓存 (交易时间1小时，非交易时间24小时)",
            variable=self.use_cache_var,
            bg='#f0f0f0',
            font=("Arial", 9)
        )
        cache_check.grid(row=2, column=0, columnspan=5, sticky=tk.W, padx=10, pady=(10, 5))

        # # 输出目录
        # tk.Label(input_frame, text="输出目录:", bg='#f0f0f0', font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W,
        #                                                                                padx=5, pady=5)
        # self.output_dir_var = tk.StringVar(value="./outputs")
        # output_dir_entry = tk.Entry(input_frame, textvariable=self.output_dir_var, font=("Arial", 10), width=40)
        # output_dir_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        # tk.Button(input_frame, text="浏览", command=self.browse_output_dir, font=("Arial", 9)).grid(row=2, column=3,
        #                                                                                             padx=5, pady=5)

        # 按钮框架
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)

        # 预测按钮
        self.predict_button = tk.Button(
            button_frame,
            text="开始预测",
            command=self.start_prediction,
            font=("Arial", 10),
            width=12,
            height=1
        )
        self.predict_button.pack(side=tk.LEFT, padx=5)

        # 查看日志按钮
        log_button = tk.Button(
            button_frame,
            text="查看日志",
            command=self.open_log_file,
            font=("Arial", 10),
            width=12,
            height=1
        )
        log_button.pack(side=tk.LEFT, padx=5)

        # 查看图表按钮
        self.view_chart_button = tk.Button(
            button_frame,
            text="查看图表",
            command=self.view_last_chart,
            font=("Arial", 10),
            width=12,
            height=1,
            state=tk.DISABLED  # 初始禁用，预测后启用
        )
        self.view_chart_button.pack(side=tk.LEFT, padx=5)

        # 清理缓存按钮
        clear_cache_button = tk.Button(
            button_frame,
            text="清理缓存",
            command=self.clear_cache,
            font=("Arial", 10),
            width=12,
            height=1
        )
        clear_cache_button.pack(side=tk.LEFT, padx=5)

        # 退出按钮
        exit_button = tk.Button(
            button_frame,
            text="退出",
            command=self.root.quit,
            font=("Arial", 10),
            width=12,
            height=1
        )
        exit_button.pack(side=tk.LEFT, padx=5)

        # 进度显示
        self.progress_frame = tk.LabelFrame(main_frame, text="预测进度", font=("Arial", 11, "bold"),
                                            bg='#f0f0f0', fg='#2c3e50')
        self.progress_frame.pack(fill=tk.X, pady=10)

        self.progress_var = tk.StringVar(value="等待开始预测...")
        progress_label = tk.Label(self.progress_frame, textvariable=self.progress_var, bg='#f0f0f0',
                                  font=("Arial", 10), wraplength=600, justify=tk.LEFT)
        progress_label.pack(padx=10, pady=10, fill=tk.X)

        # 进度条
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

        # 日志显示复选框
        log_check_frame = tk.Frame(main_frame, bg='#f0f0f0')
        log_check_frame.pack(fill=tk.X, pady=5)
        
        self.show_log_var = tk.BooleanVar(value=False)
        self.show_log_check = tk.Checkbutton(
            log_check_frame,
            text="显示实时日志",
            variable=self.show_log_var,
            command=self.toggle_log_display,
            bg='#f0f0f0',
            font=("Arial", 10)
        )
        self.show_log_check.pack(side=tk.LEFT, padx=10)

        # 结果展示区域
        self.result_frame = tk.LabelFrame(main_frame, text="预测结果", font=("Arial", 11, "bold"),
                                          bg='#f0f0f0', fg='#2c3e50')
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.result_text = tk.Text(self.result_frame, height=8, font=("Arial", 9), wrap=tk.WORD)
        scrollbar = tk.Scrollbar(self.result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # 日志显示区域（初始隐藏）
        self.log_frame = tk.LabelFrame(main_frame, text="实时日志", font=("Arial", 11, "bold"),
                                       bg='#f0f0f0', fg='#2c3e50')
        # 不立即pack，等待用户勾选复选框
        
        self.log_text = tk.Text(self.log_frame, height=10, font=("Consolas", 9), wrap=tk.WORD,
                                bg='#1e1e1e', fg='#d4d4d4', insertbackground='white')
        log_scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # 初始化图表窗口（独立窗口）
        self.chart_window = None
        self.figure = None
        self.canvas = None
        self.toolbar = None
        
        # 保存最后一次预测的数据，用于重新显示图表
        self.last_prediction_data = None

    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)

    def toggle_log_display(self):
        """切换日志显示/隐藏"""
        if self.show_log_var.get():
            # 显示日志区域
            self.log_frame.pack(fill=tk.BOTH, expand=True, pady=10, before=self.result_frame)
            logger.info("📋 日志显示已开启")
        else:
            # 隐藏日志区域
            self.log_frame.pack_forget()
            logger.info("📋 日志显示已关闭")

    def on_stock_code_changed(self, *args):
        """股票代码变化时自动获取名称"""
        stock_code = self.stock_code_var.get().strip()
        
        # 只有当代码是6位数字时才自动获取
        if len(stock_code) == 6 and stock_code.isdigit():
            # 延迟1000ms后执行，避免频繁请求（增加到1秒）
            if hasattr(self, '_fetch_timer'):
                self.root.after_cancel(self._fetch_timer)
            
            self._fetch_timer = self.root.after(1000, lambda: self._auto_fetch_name(stock_code))
    
    def _auto_fetch_name(self, stock_code):
        """后台自动获取股票名称"""
        # 显示获取中状态
        self.name_status_var.set("⏳ 获取中...")
        self.root.update()
        
        try:
            # 在新线程中获取
            def fetch_thread():
                stock_name = _fetch_stock_name(stock_code)
                # 在主线程中更新
                self.root.after(0, lambda: self._on_name_fetched(stock_code, stock_name))
            
            thread = threading.Thread(target=fetch_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"❌ 自动获取失败: {e}")
            self.name_status_var.set("❌ 失败")
    
    def _on_name_fetched(self, stock_code, stock_name):
        """名称获取完成后的回调"""
        if not stock_name.startswith("股票"):
            # 成功获取
            self.stock_name_var.set(stock_name)
            self.name_status_var.set("✅ 已自动获取")
            logger.info(f"✅ 自动获取 {stock_code} 名称: {stock_name}")
            
            # 3秒后清除状态
            self.root.after(3000, lambda: self.name_status_var.set(""))
        else:
            # 获取失败
            self.name_status_var.set("⚠️ 请手动输入")
            logger.warning(f"⚠️ 未能自动获取 {stock_code} 的名称")

    def open_log_file(self):
        """打开日志文件"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        if not os.path.exists(log_dir):
            messagebox.showinfo("提示", "日志目录不存在，请先运行预测")
            return
        
        # 获取最新的日志文件
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if not log_files:
            messagebox.showinfo("提示", "没有找到日志文件")
            return
        
        # 按修改时间排序，获取最新的
        latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
        log_path = os.path.join(log_dir, latest_log)
        
        try:
            # Windows 下用记事本打开
            os.startfile(log_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开日志文件: {e}")

    def view_last_chart(self):
        """查看上一次的预测图表"""
        if self.last_prediction_data is None:
            messagebox.showinfo("提示", "还没有进行过预测，请先运行预测")
            return
        
        # 使用保存的数据重新显示图表（在主线程中）
        try:
            data = self.last_prediction_data
            self.display_chart(
                data['historical_df'],
                data['pred_df'],
                data['future_dates'],
                data['stock_code'],
                data['stock_name']
            )
        except Exception as e:
            messagebox.showerror("错误", f"无法显示图表：{e}")
            logger.error(f"显示图表失败: {e}", exc_info=True)

    def clear_cache(self):
        """清理数据缓存"""
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        if not os.path.exists(cache_dir):
            messagebox.showinfo("提示", "缓存目录不存在")
            return
        
        try:
            import shutil
            file_count = len([f for f in os.listdir(cache_dir) if f.endswith('.csv')])
            if file_count == 0:
                messagebox.showinfo("提示", "没有缓存文件")
                return
            
            # 确认删除
            if messagebox.askyesno("确认", f"确定要删除 {file_count} 个缓存文件吗？\n\n这将导致下次预测时重新从网络获取数据。"):
                shutil.rmtree(cache_dir)
                messagebox.showinfo("完成", f"已清理 {file_count} 个缓存文件")
                logger.info(f"🗑️ 已清理缓存目录: {cache_dir}")
        except Exception as e:
            messagebox.showerror("错误", f"清理缓存失败: {e}")
            logger.error(f"清理缓存失败: {e}", exc_info=True)

    def start_prediction(self):
        """开始预测"""
        if not self.validate_inputs():
            return

        self.predict_button.config(state=tk.DISABLED)
        self.view_chart_button.config(state=tk.DISABLED)  # 禁用查看图表按钮
        self.result_text.delete(1.0, tk.END)
        self.progress_bar.start()

        prediction_thread = threading.Thread(target=self.run_prediction)
        prediction_thread.daemon = True
        prediction_thread.start()

    def validate_inputs(self):
        """验证输入参数"""
        try:
            stock_code = self.stock_code_var.get().strip()
            stock_name = self.stock_name_var.get().strip()
            pred_days = int(self.pred_days_var.get())
            history_years = int(self.history_years_var.get())

            if not stock_code or not stock_name:
                messagebox.showerror("错误", "请输入股票代码和名称")
                return False

            if pred_days <= 0 or pred_days > 365:
                messagebox.showerror("错误", "预测天数应在1-365天之间")
                return False

            if history_years <= 0 or history_years > 10:
                messagebox.showerror("错误", "历史年限应在1-10年之间")
                return False

            return True

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return False

    def run_prediction(self):
        """运行预测流程"""
        try:
            stock_code = self.stock_code_var.get().strip()
            stock_name = self.stock_name_var.get().strip()
            pred_days = int(self.pred_days_var.get())
            history_years = int(self.history_years_var.get())
            # 使用默认输出目录
            output_dir = "./outputs"
            
            # 如果股票名称仍为空，尝试自动获取
            stock_name = self.stock_name_var.get().strip()
            if not stock_name or stock_name.startswith("股票"):
                self.update_progress(f"🔄 正在获取 {stock_code} 的股票名称...")
                stock_name = _fetch_stock_name(stock_code)
                self.stock_name_var.set(stock_name)
                logger.info(f"✅ 自动设置股票名称: {stock_name}")
            
            # 获取缓存设置
            use_cache = self.use_cache_var.get()

            self.update_progress(f"🎯 开始 {stock_name}({stock_code}) 预测流程")
            if use_cache:
                self.update_progress("💾 缓存模式：交易时间1小时，非交易时间24小时")
            else:
                self.update_progress("🔄 实时模式：每次都从网络获取最新数据")

            success, result = run_stock_prediction(
                stock_code, stock_name, pred_days, output_dir, history_years, use_cache,
                progress_callback=self.update_progress,
                result_callback=self.update_result
            )

            if success:
                self.update_progress("✅ 预测完成！")
                # 启用查看图表按钮
                self.root.after(0, lambda: self.view_chart_button.config(state=tk.NORMAL))
                messagebox.showinfo("完成", f"{stock_name}({stock_code})预测完成！\n可以点击“📊 查看图表”按钮重新打开图表窗口")
            else:
                self.update_progress("❌ 预测失败")
                messagebox.showerror("错误", f"预测失败: {result}")

        except Exception as e:
            self.update_progress(f"❌ 预测过程出现错误: {str(e)}")
            messagebox.showerror("错误", f"预测过程出现错误: {str(e)}")
        finally:
            self.root.after(0, lambda: self.predict_button.config(state=tk.NORMAL))
            self.root.after(0, self.progress_bar.stop)

    def update_progress(self, message):
        """更新进度信息"""
        self.root.after(0, lambda: self.progress_var.set(message))
        logger.info(message)

    def update_result(self, message):
        """更新结果信息"""
        self.root.after(0, lambda: self.result_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.result_text.see(tk.END))

    def display_chart(self, historical_df, pred_df, future_dates, stock_code, stock_name):
        """在独立窗口中显示交互式图表"""
        try:
            # 保存预测数据以便重新显示
            self.last_prediction_data = {
                'historical_df': historical_df,
                'pred_df': pred_df,
                'future_dates': future_dates,
                'stock_code': stock_code,
                'stock_name': stock_name
            }
            
            # 如果窗口已存在，先关闭
            if self.chart_window is not None:
                try:
                    self.chart_window.destroy()
                except:
                    pass
            
            # 创建新窗口
            self.chart_window = tk.Toplevel(self.root)
            self.chart_window.title(f"{stock_name}({stock_code}) - 预测图表")
            self.chart_window.geometry("1200x800")
            self.chart_window.configure(bg='#f0f0f0')
            
            # 设置窗口图标（可选）
            try:
                self.chart_window.iconbitmap(default='')
            except:
                pass
            
            # 创建图表框架
            chart_frame = tk.Frame(self.chart_window, bg='white')
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 创建新图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=100)
            fig.suptitle(f'{stock_name}({stock_code}) - 股票价格预测', fontsize=16, fontweight='bold')

            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False

            # 价格图
            ax1.plot(historical_df['timestamps'], historical_df['close'],
                     color='#1f77b4', linewidth=2.5, label='历史价格')
            ax1.plot(future_dates, pred_df['close'],
                     color='#ff7f0e', linewidth=2.5, linestyle='--', label='预测价格')

            current_price = historical_df['close'].iloc[-1]
            final_price = pred_df['close'].iloc[-1]
            change_pct = ((final_price - current_price) / current_price) * 100

            ax1.set_ylabel('收盘价 (元)', fontsize=12, fontweight='bold')
            ax1.legend(loc='best', fontsize=10)
            ax1.grid(True, alpha=0.3)
            ax1.set_title(f'当前价: {current_price:.2f}元 | 预测价: {final_price:.2f}元 ({change_pct:+.2f}%)',
                          fontweight='bold', fontsize=13, color='#2c3e50')

            # 成交量图
            ax2.bar(historical_df['timestamps'], historical_df['volume'],
                    alpha=0.6, color='#1f77b4', label='历史成交量')
            ax2.bar(future_dates, pred_df['volume'],
                    alpha=0.6, color='#ff7f0e', label='预测成交量')

            ax2.set_ylabel('成交量', fontsize=12, fontweight='bold')
            ax2.set_xlabel('日期', fontsize=12, fontweight='bold')
            ax2.legend(loc='best', fontsize=10)
            ax2.grid(True, alpha=0.3)
            ax2.set_title('成交量预测', fontweight='bold', fontsize=13, color='#2c3e50')

            # 格式化 x 轴日期
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=8)

            plt.tight_layout()

            # 嵌入到 Tkinter 独立窗口
            self.figure = fig
            self.canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            self.canvas.draw()

            # 添加工具栏（缩放、平移、保存等功能）
            self.toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
            self.toolbar.update()

            # 放置画布
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            logger.info("✅ 交互式图表窗口已打开")
            print("✅ 交互式图表窗口已打开")

        except Exception as e:
            error_msg = f"❌ 显示图表失败: {e}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            messagebox.showerror("错误", f"无法显示图表：{e}")


def _fetch_stock_name(stock_code, max_retries=3):
    """自动获取股票名称，多数据源fallback机制"""
    import time
    import random
    
    # 检查缓存
    if stock_code in stock_name_cache:
        cached_name = stock_name_cache[stock_code]
        logger.info(f"📁 使用缓存的股票名称: {stock_code} -> {cached_name}")
        return cached_name
    
    # 多数据源尝试获取股票名称
    name_sources = [
        {'name': 'AKShare-东方财富', 'func': _fetch_name_from_akshare_em},
        {'name': 'AKShare-新浪全市场', 'func': _fetch_name_from_akshare_sina},
        {'name': 'BaoStock', 'func': _fetch_name_from_baostock},
    ]
    
    for source in name_sources:
        try:
            logger.info(f"🔄 尝试从 {source['name']} 获取股票名称...")
            stock_name = source['func'](stock_code)
            
            if stock_name and not stock_name.startswith("股票"):
                logger.info(f"✅ 从 {source['name']} 获取股票名称: {stock_name}")
                stock_name_cache[stock_code] = stock_name
                return stock_name
            else:
                logger.warning(f"⚠️ {source['name']} 未找到股票名称")
        except Exception as e:
            logger.warning(f"⚠️ {source['name']} 获取失败: {e}")
            continue
    
    # 所有数据源都失败
    logger.error(f"❌ 所有数据源都无法获取 {stock_code} 的名称")
    return f"股票{stock_code}"


def fetch_stock_data(stock_code, adjust="qfq", max_retries=5, use_cache=True):
    """获取股票数据，使用统一数据源管理器"""
    import time
    
    # 验证股票代码格式
    if not stock_code or len(stock_code) not in [6, 7]:
        logger.error(f"❌ 无效的股票代码: {stock_code}")
        return None
    
    # 尝试从缓存加载（仅在非交易时间或缓存很新时使用）
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    cache_file = os.path.join(cache_dir, f"{stock_code}_{adjust}.csv")
    
    if use_cache and os.path.exists(cache_file):
        try:
            # 检查当前是否为交易时间
            now = datetime.now()
            is_trading_time = (
                now.weekday() < 5 and  # 周一到周五
                ((now.hour >= 9 and now.minute >= 30) or (now.hour >= 10)) and  # 9:30后
                now.hour < 15  # 15:00前
            )
            
            # 检查缓存文件年龄
            file_age = time.time() - os.path.getmtime(cache_file)
            file_age_hours = file_age / 3600
            
            # 缓存策略：
            # 1. 交易时间内：只使用1小时内的缓存
            # 2. 非交易时间：使用当天收盘后的缓存（最多24小时）
            max_age_hours = 1 if is_trading_time else 24
            
            if file_age_hours < max_age_hours:
                logger.info(f"📁 使用缓存数据 ({file_age_hours:.1f}小时前): {cache_file}")
                print(f"📁 使用缓存数据 ({file_age_hours:.1f}小时前)")
                df = pd.read_csv(cache_file, encoding='utf-8-sig')
                df['timestamps'] = pd.to_datetime(df['timestamps'])
                return df
            else:
                if is_trading_time:
                    logger.info("⏰ 交易时间，缓存已过期(>1小时)，将重新获取最新数据")
                else:
                    logger.info("⏰ 缓存已过期(>24小时)，将重新获取数据")
        except Exception as e:
            logger.warning(f"⚠️ 读取缓存失败: {e}，将重新获取")
    
    # 使用统一数据源管理器
    if DataSourceManager is not None:
        try:
            logger.info("🔄 使用统一数据源管理器获取数据...")
            manager = DataSourceManager()
            df = manager.fetch(stock_code, adjust)
            
            if df is not None and not df.empty:
                logger.info(f"✅ 成功获取 {len(df)} 条数据")
                
                # 保存到缓存
                if use_cache:
                    try:
                        os.makedirs(cache_dir, exist_ok=True)
                        df.to_csv(cache_file, index=False, encoding='utf-8-sig')
                        logger.info(f"💾 数据已缓存: {cache_file}")
                    except Exception as e:
                        logger.warning(f"⚠️ 缓存保存失败: {e}")
                
                return df
            else:
                logger.error("❌ 数据源管理器返回空数据")
                return None
        except Exception as e:
            logger.error(f"❌ 数据源管理器异常: {e}，回退到旧版方式")
    
    # 回退到旧版多数据源逻辑（兼容性保障）
    logger.warning("⚠️ 使用旧版数据获取逻辑")
    return _fetch_stock_data_legacy(stock_code, adjust, max_retries)


def _fetch_stock_data_legacy(stock_code, adjust="qfq", max_retries=5):
    """旧版数据获取逻辑（兼容性保障）"""
    import random
    
    # 多数据源尝试
    data_sources = [
        {
            'name': 'AKShare-东方财富',
            'func': _fetch_from_akshare,
            'priority': 1
        },
        {
            'name': 'AKShare-新浪财经', 
            'func': _fetch_from_sina,
            'priority': 2
        },
        {
            'name': '模拟数据生成器',
            'func': _generate_fallback_data,
            'priority': 3
        }
    ]
    
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    cache_file = os.path.join(cache_dir, f"{stock_code}_{adjust}.csv")
    
    # 按优先级尝试每个数据源
    for source in sorted(data_sources, key=lambda x: x['priority']):
        try:
            logger.info(f"🔄 尝试数据源: {source['name']}")
            print(f"🔄 尝试数据源: {source['name']}")
            
            df = source['func'](stock_code, adjust, max_retries)
            
            if df is not None and not df.empty:
                logger.info(f"✅ 成功从 {source['name']} 获取数据")
                print(f"✅ 成功从 {source['name']} 获取 {len(df)} 条数据")
                
                # 标准化数据结构
                df = _standardize_dataframe(df, stock_code)
                
                # 保存到缓存
                if df is not None:
                    try:
                        os.makedirs(cache_dir, exist_ok=True)
                        df.to_csv(cache_file, index=False, encoding='utf-8-sig')
                        logger.info(f"💾 数据已缓存: {cache_file}")
                    except Exception as e:
                        logger.warning(f"⚠️ 缓存保存失败: {e}")
                
                return df
            else:
                logger.warning(f"⚠️ {source['name']} 返回空数据")
                
        except Exception as e:
            logger.warning(f"⚠️ {source['name']} 失败: {e}")
            continue
    
    logger.error(f"❌ 所有数据源都失败，无法获取 {stock_code} 的数据")
    return None


def _fetch_name_from_akshare_em(stock_code):
    """从AKShare-东方财富获取股票名称"""
    import time
    import random
    
    time.sleep(random.uniform(0.3, 0.8))
    
    stock_info = ak.stock_individual_info_em(symbol=stock_code)
    
    if not stock_info.empty and 'value' in stock_info.columns:
        name_row = stock_info[stock_info['item'] == '股票简称']
        if not name_row.empty:
            return name_row['value'].iloc[0]
    
    return None


def _fetch_name_from_akshare_sina(stock_code):
    """从AKShare-新浪全市场获取股票名称"""
    import time
    
    time.sleep(0.5)
    
    stock_zh_a_spot_df = ak.stock_zh_a_spot_em()
    matched = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == stock_code]
    
    if not matched.empty:
        return matched['名称'].iloc[0]
    
    return None


def _fetch_name_from_baostock(stock_code):
    """从BaoStock获取股票名称"""
    try:
        import baostock as bs
        
        # 登录
        lg = bs.login()
        if lg.error_code != '0':
            return None
        
        # 格式化股票代码
        if stock_code.startswith(('6', '9')):
            full_code = f"sh.{stock_code}"
        else:
            full_code = f"sz.{stock_code}"
        
        # 查询股票基本信息
        rs = bs.query_stock_basic(code=full_code)
        
        # 登出
        bs.logout()
        
        if rs.error_code != '0':
            return None
        
        # 解析结果
        while (rs.error_code == '0') and rs.next():
            row_data = rs.get_row_data()
            if len(row_data) > 1:
                stock_name = row_data[1]  # 股票名称在第2个字段
                if stock_name and stock_name.strip():
                    return stock_name.strip()
        
        return None
        
    except ImportError:
        logger.debug("BaoStock未安装，跳过")
        return None
    except Exception as e:
        logger.debug(f"BaoStock获取名称失败: {e}")
        return None


def _fetch_from_akshare(stock_code, adjust="qfq", max_retries=3):
    """从 AKShare-东方财富 获取数据（主数据源）"""
    import time
    import random
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"📡 [AKShare] 正在获取 {stock_code}... (尝试 {attempt}/{max_retries})")
            
            # 添加随机延迟
            if attempt > 1:
                base_delay = 3 * attempt
                jitter = random.uniform(0.5, 2.0)
                delay = base_delay + jitter
                logger.info(f"⏳ 等待 {delay:.1f} 秒后重试...")
                time.sleep(delay)
            else:
                time.sleep(random.uniform(0.5, 1.5))
            
            df = ak.stock_zh_a_hist(
                symbol=stock_code, 
                period="daily", 
                adjust=adjust,
                start_date="20200101",
                end_date="20261231"
            )

            if df is None or df.empty:
                logger.warning(f"❌ [AKShare] 未获取到数据")
                if attempt < max_retries:
                    continue
                return None

            # 列映射
            column_mapping = {
                '日期': 'timestamps',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_chg'
            }

            actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=actual_mapping)
            
            if 'timestamps' not in df.columns:
                logger.error("❌ [AKShare] 缺少必要列")
                return None
            
            df['timestamps'] = pd.to_datetime(df['timestamps'])
            df = df.sort_values('timestamps').reset_index(drop=True)
            
            logger.info(f"✅ [AKShare] 成功获取 {len(df)} 条数据")
            return df

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ [AKShare] 失败 (尝试 {attempt}/{max_retries}): {error_msg}")
            
            if 'Connection' in error_msg or 'RemoteDisconnected' in error_msg:
                logger.warning("💡 [AKShare] 网络问题，将重试...")
            elif '403' in error_msg or 'Forbidden' in error_msg:
                logger.warning("💡 [AKShare] IP可能被限制")
                return None  # 403不需要重试
            
            if attempt < max_retries:
                continue
            return None
    
    return None


def _fetch_from_sina(stock_code, adjust="qfq", max_retries=2):
    """从 AKShare-新浪财经 获取数据（备用数据源）"""
    import time
    
    try:
        logger.info(f"📡 [Sina] 正在获取 {stock_code}...")
        time.sleep(1)  # 延迟避免请求过快
        
        # 使用新浪接口
        df = ak.stock_zh_a_daily(symbol=stock_code, adjust=adjust)
        
        if df is None or df.empty:
            logger.warning("❌ [Sina] 未获取到数据")
            return None
        
        # 列映射
        column_mapping = {
            'date': 'timestamps',
            'open': 'open',
            'close': 'close',
            'high': 'high',
            'low': 'low',
            'volume': 'volume'
        }
        
        actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=actual_mapping)
        
        if 'timestamps' not in df.columns:
            logger.error("❌ [Sina] 缺少必要列")
            return None
        
        df['timestamps'] = pd.to_datetime(df['timestamps'])
        df = df.sort_values('timestamps').reset_index(drop=True)
        
        # 计算成交额（如果缺失）
        if 'amount' not in df.columns and 'close' in df.columns and 'volume' in df.columns:
            df['amount'] = df['close'] * df['volume']
        
        logger.info(f"✅ [Sina] 成功获取 {len(df)} 条数据")
        return df
        
    except Exception as e:
        logger.error(f"❌ [Sina] 失败: {e}")
        return None


def _generate_fallback_data(stock_code, adjust="qfq", max_retries=1):
    """生成模拟数据（最后备选方案）"""
    try:
        logger.warning(f"⚠️ [Fallback] 所有API失败，生成模拟数据用于测试")
        
        # 基于真实价格的参考数据
        real_stock_references = {
            '600580': {'name': '卧龙电驱', 'current_price': 38.54, 'range': (30.0, 50.0)},
            '300207': {'name': '欣旺达', 'current_price': 33.79, 'range': (28.0, 45.0)},
            '000001': {'name': '平安银行', 'current_price': 12.50, 'range': (10.0, 16.0)},
        }
        
        stock_info = real_stock_references.get(stock_code, {
            'name': f'股票{stock_code}',
            'current_price': 20.0,
            'range': (15.0, 30.0)
        })
        
        # 生成最近1年的交易日数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        dates = pd.bdate_range(start=start_date, end=end_date, freq='B')
        
        np.random.seed(42)
        n_points = len(dates)
        current_price = stock_info['current_price']
        min_price, max_price = stock_info['range']
        
        # 反向生成价格序列
        prices = [current_price]
        for i in range(1, n_points):
            volatility = 0.02
            historical_return = np.random.normal(-0.0002, volatility)
            prev_price = prices[0] * (1 + historical_return)
            prev_price = max(min_price * 0.9, min(max_price * 1.1, prev_price))
            prices.insert(0, prev_price)
        
        # 生成OHLC数据
        stock_data = []
        for i, date in enumerate(dates):
            close_price = prices[i]
            daily_volatility = abs(np.random.normal(0, 0.015))
            open_price = close_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, close_price) * (1 + daily_volatility)
            low_price = min(open_price, close_price) * (1 - daily_volatility)
            
            high_price = max(open_price, close_price, low_price, high_price)
            low_price = min(open_price, close_price, high_price, low_price)
            
            volume = int(abs(np.random.normal(1500000, 400000)))
            amount = volume * close_price
            
            pct_chg = ((close_price - prices[i-1]) / prices[i-1]) * 100 if i > 0 else 0
            
            stock_data.append({
                'timestamps': date,
                'stock_code': stock_code,
                'open': round(open_price, 2),
                'close': round(close_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'volume': volume,
                'amount': round(amount, 2),
                'pct_chg': round(pct_chg, 2)
            })
        
        df = pd.DataFrame(stock_data)
        logger.warning(f"⚠️ [Fallback] 已生成 {len(df)} 条模拟数据（仅供参考）")
        print("⚠️ 注意：使用的是模拟数据，预测结果可能不准确！")
        return df
        
    except Exception as e:
        logger.error(f"❌ [Fallback] 生成失败: {e}")
        return None


def _standardize_dataframe(df, stock_code):
    """标准化DataFrame结构，确保所有数据源输出一致"""
    try:
        # 确保必要的列存在
        required_columns = ['timestamps', 'open', 'high', 'low', 'close', 'volume']
        
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"❌ 缺少必要列: {col}")
                return None
        
        # 添加缺失的列（如果有）
        if 'amount' not in df.columns:
            df['amount'] = df['close'] * df['volume']
        
        if 'pct_chg' not in df.columns and len(df) > 1:
            df['pct_chg'] = df['close'].pct_change() * 100
        
        # 确保数据类型正确
        df['timestamps'] = pd.to_datetime(df['timestamps'])
        df = df.sort_values('timestamps').reset_index(drop=True)
        df['stock_code'] = stock_code
        
        # 选择标准列
        standard_columns = ['timestamps', 'stock_code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
        available_columns = [col for col in standard_columns if col in df.columns]
        df = df[available_columns]
        
        logger.info(f"✅ 数据结构标准化完成: {len(df)} 条记录, {len(available_columns)} 个字段")
        return df
        
    except Exception as e:
        logger.error(f"❌ 数据标准化失败: {e}")
        return None


def prepare_data(df, history_years=1):
    """准备数据"""
    if history_years > 0:
        cutoff_date = datetime.now() - timedelta(days=history_years * 365)
        df = df[df['timestamps'] >= cutoff_date]
        logger.info(f"📅 使用最近 {history_years} 年数据: {len(df)} 条记录")
        print(f"📅 使用最近 {history_years} 年数据: {len(df)} 条记录")

    current_price = df['close'].iloc[-1]
    logger.info(f"✅ 当前价格: {current_price:.2f}元")
    logger.info(f"📈 价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    print(f"✅ 当前价格: {current_price:.2f}元")
    print(f"📈 价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")

    return df


def generate_trading_dates(last_date, pred_len):
    """生成交易日"""
    holidays_2025 = [
        '2025-01-01', '2025-01-27', '2025-01-28', '2025-01-29', '2025-01-30',
        '2025-01-31', '2025-02-01', '2025-02-02', '2025-04-04', '2025-04-05',
        '2025-04-06', '2025-05-01', '2025-05-02', '2025-05-03', '2025-06-08',
        '2025-06-09', '2025-06-10', '2025-10-01', '2025-10-02', '2025-10-03',
        '2025-10-04', '2025-10-05', '2025-10-06', '2025-10-07',
    ]
    holidays = [datetime.strptime(date, '%Y-%m-%d').date() for date in holidays_2025]

    trading_dates = []
    current_date = last_date + timedelta(days=1)

    while len(trading_dates) < pred_len:
        if current_date.weekday() < 5 and current_date.date() not in holidays:
            trading_dates.append(current_date)
        current_date += timedelta(days=1)

    logger.info(f"📅 生成 {len(trading_dates)} 个交易日")
    print(f"📅 生成 {len(trading_dates)} 个交易日")
    return trading_dates


def plot_prediction(historical_df, pred_df, future_dates, stock_code, stock_name, output_dir):
    """绘制预测图表"""
    os.makedirs(output_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle(f'{stock_name}({stock_code}) - 股票价格预测', fontsize=16, fontweight='bold')

    # 价格图
    ax1.plot(historical_df['timestamps'], historical_df['close'],
             color='#1f77b4', linewidth=2, label='历史价格')
    ax1.plot(future_dates, pred_df['close'],
             color='#ff7f0e', linewidth=2, linestyle='--', label='预测价格')

    current_price = historical_df['close'].iloc[-1]
    final_price = pred_df['close'].iloc[-1]
    change_pct = ((final_price - current_price) / current_price) * 100

    ax1.set_ylabel('收盘价 (元)', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_title(f'价格走势预测 - 当前价: {current_price:.2f}元, 预测价: {final_price:.2f}元 ({change_pct:+.2f}%)',
                  fontweight='bold')

    # 成交量图
    ax2.bar(historical_df['timestamps'], historical_df['volume'],
            alpha=0.6, color='#1f77b4', label='历史成交量')
    ax2.bar(future_dates, pred_df['volume'],
            alpha=0.6, color='#ff7f0e', label='预测成交量')

    ax2.set_ylabel('成交量', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_title('成交量预测', fontweight='bold')

    plt.tight_layout()

    chart_path = os.path.join(output_dir, f'{stock_code}_prediction.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"📊 预测图表已保存: {chart_path}")
    print(f"📊 预测图表已保存: {chart_path}")
    return chart_path


def run_stock_prediction(stock_code, stock_name, pred_days, output_dir, history_years=1, use_cache=True,
                         progress_callback=None, result_callback=None):
    """运行股票预测"""
    logger.info(f"="*60)
    logger.info(f"开始预测: {stock_name}({stock_code})")
    logger.info(f"预测天数: {pred_days}, 历史年限: {history_years}")
    logger.info(f"使用缓存: {use_cache}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"="*60)

    def update_progress(message):
        if progress_callback:
            progress_callback(message)
        logger.info(message)

    def update_result(message):
        if result_callback:
            result_callback(message)
        logger.info(message)

    try:
        update_progress(f"🎯 开始 {stock_name}({stock_code}) 预测")
        update_progress("=" * 50)

        # 1. 获取数据
        update_progress("\n步骤1: 获取股票数据...")
        df = fetch_stock_data(stock_code, use_cache=use_cache)
        if df is None:
            update_result("❌ 无法获取股票数据")
            return False, "无法获取数据"

        # 2. 准备数据
        update_progress("步骤2: 准备数据...")
        df = prepare_data(df, history_years)

        # 3. 加载模型
        update_progress("步骤3: 加载Kronos模型...")
        try:
            tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
            model = Kronos.from_pretrained("NeoQuasar/Kronos-base")
            predictor = KronosPredictor(model, tokenizer, device=None, max_context=512)
            update_progress("✅ 模型加载完成")
        except Exception as e:
            error_msg = f"❌ 模型加载失败: {e}"
            update_result(error_msg)
            return False, error_msg

        # 4. 计算参数
        update_progress("步骤4: 计算预测参数...")
        lookback = min(200, len(df) - pred_days)
        lookback = max(100, lookback)
        pred_len = min(pred_days, len(df) - lookback)

        if pred_len <= 0:
            update_result("❌ 数据量不足")
            return False, "数据量不足"

        update_progress(f"✅ 回看期: {lookback}, 预测期: {pred_len}")

        # 5. 准备输入数据
        update_progress("步骤5: 准备输入数据...")
        x_df = df.loc[-lookback:, ['open', 'high', 'low', 'close', 'volume', 'amount']].reset_index(drop=True)
        x_timestamp = df.loc[-lookback:, 'timestamps'].reset_index(drop=True)

        last_date = df['timestamps'].iloc[-1]
        future_dates = generate_trading_dates(last_date, pred_len)

        # 6. 执行预测
        update_progress("步骤6: 执行预测...")
        pred_df = predictor.predict(
            df=x_df,
            x_timestamp=x_timestamp,
            y_timestamp=pd.Series(future_dates),
            pred_len=pred_len,
            T=1.0,
            top_p=0.9,
            sample_count=1,
            verbose=True
        )

        update_progress("✅ 预测完成")

        # 7. 绘制图表
        update_progress("步骤7: 生成预测图表...")
        historical_df = df.loc[-lookback:].reset_index(drop=True)
        chart_path = plot_prediction(historical_df, pred_df, future_dates,
                                     stock_code, stock_name, output_dir)

        # 8. 在 GUI 中显示交互式图表（在主线程中）
        if hasattr(progress_callback, '__self__'):
            app_instance = progress_callback.__self__
            if hasattr(app_instance, 'display_chart'):
                update_progress("步骤8: 显示交互式图表...")
                # 使用 root.after 确保在主线程中创建图表窗口
                app_instance.root.after(0, app_instance.display_chart, 
                                       historical_df, pred_df, future_dates, stock_code, stock_name)

        # 9. 输出结果
        current_price = historical_df['close'].iloc[-1]
        predicted_price = pred_df['close'].iloc[-1]
        change_pct = ((predicted_price - current_price) / current_price) * 100

        update_result(f"\n📈 {stock_name}({stock_code}) 预测结果")
        update_result("=" * 50)
        update_result(f"当前价格: {current_price:.2f} 元")
        update_result(f"预测价格: {predicted_price:.2f} 元 ({change_pct:+.2f}%)")
        update_result(f"预测天数: {pred_len} 个交易日")
        update_result(f"图表保存: {chart_path}")

        # 保存预测数据
        prediction_data = pd.DataFrame({
            '日期': future_dates,
            '预测收盘价': pred_df['close'].values,
            '预测成交量': pred_df['volume'].values
        })
        csv_path = os.path.join(output_dir, f'{stock_code}_predictions.csv')
        prediction_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
        update_progress(f"💾 预测数据已保存: {csv_path}")

        update_progress(f"\n🎉 预测完成!")
        return True, "预测完成"

    except Exception as e:
        error_msg = f"❌ 预测错误: {e}"
        logger.error(error_msg, exc_info=True)
        update_result(error_msg)
        return False, error_msg


def main():
    """主函数"""
    root = tk.Tk()
    app = StockPredictorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
