import tkinter as tk
from tkinter import ttk, messagebox, font
from PIL import Image, ImageTk
import numpy as np
import json
import io
import win32clipboard
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
import os
import subprocess

# 配置常量
VECTOR_FILE = os.path.join(os.path.dirname(__file__), "vectors.npy")  # 相对路径
META_FILE = os.path.join(os.path.dirname(__file__), "metadata.json")  # 相对路径
PICT_DIR = os.path.join(os.path.dirname(__file__), "pict")  # 图片文件夹
CUSTOM_FONT_PATH = r"D:\synchronize\工具\圆体-简繁 常规体.ttc"

# 可调整参数配置
CONFIG = {
    # 字体相关
    'font': {
        'family': '圆体-简繁 常规体',  # 主字体
        'fallback': '微软雅黑',       # 备用字体
        'sizes': {
            'entry': 12,             # 输入框字体大小
            'score': 9,              # 相似度字体大小
            'text': 8,               # 原始文本字体大小
            'button': 8,             # 按钮字体大小
            'search_button': 12      # 搜索按钮字体大小
        },
        'colors': {
            'score': '#2d3436',      # 相似度文字颜色
            'text': '#636e72',       # 原始文本颜色
            'button_text': 'black'   # 按钮文字颜色
        }
    },
    
    # 布局相关
    'layout': {
        'window_size': "1080x800",   # 窗口大小
        'entry_width': 20,           # 输入框宽度（字符数）
        'button': {
            'width': 10,             # 按钮宽度（像素）
            'height': 1              # 按钮高度（行数）
        },
        'image': {
            'width': 300,            # 图片显示宽度
            'height': 180            # 图片显示高度
        },
        'wraplength': 280            # 文本换行长度
    },
    
    # 颜色主题
    'colors': {
        'background': '#f0f0f0',     # 背景色
        'button': {
            'search': '#0984e3',     # 搜索按钮颜色
            'copy': '#00b894'        # 复制按钮颜色
        }
    }
}

def count_image_files(directory):
    """递归统计目录及其子目录中的图片文件数"""
    image_count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_count += 1
    return image_count

def check_and_preprocess():
    """检查 metadata 条数是否与 pict 文件夹中的文件数一致，如果不一致则运行预处理"""
    if not os.path.exists(PICT_DIR):
        print(f"❌ 图片文件夹 {PICT_DIR} 不存在")
        return False

    # 获取 pict 文件夹及其子文件夹中的图片文件数
    pict_file_count = count_image_files(PICT_DIR)

    # 检查 metadata.json 是否存在
    if not os.path.exists(META_FILE):
        print("❌ metadata.json 不存在，开始预处理...")
        run_preprocess()
        return True

    # 检查 metadata.json 的条数
    with open(META_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    metadata_count = len(metadata["paths"])

    # 如果条数不一致，运行预处理
    if pict_file_count != metadata_count:
        print(f"❌ 文件数不一致（pict: {pict_file_count}, metadata: {metadata_count}），开始预处理...")
        run_preprocess()
        return True

    print("✅ 文件数一致，无需预处理")
    return True

def run_preprocess():
    """运行预处理脚本"""
    try:
        # 调用 preprocess_from_filenames.py
        subprocess.run(["python", "preprocess_from_filenames.py"], check=True)
        print("✅ 预处理完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 预处理失败: {str(e)}")
        raise

class SubtitleSearcher:
    def __init__(self, root_dir="pict"):
        """初始化搜索器"""
        self.root_dir = os.path.join(os.path.dirname(__file__), root_dir)  # 相对路径
        try:
            self.embeddings = np.load(VECTOR_FILE)
            with open(META_FILE, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ 系统初始化完成")
            print(f"已加载 {len(self.metadata['paths'])} 条索引数据")
        except Exception as e:
            print(f"❌ 初始化失败: {str(e)}")
            raise

    def search(self, query, top_k=6, threshold=0.3):
        """执行搜索"""
        try:
            query_vec = self.model.encode([query])
            similarities = cosine_similarity(query_vec, self.embeddings)[0]
            sorted_indices = np.argsort(similarities)[::-1][:top_k]
            return [{
                "score": float(similarities[i]),
                "text": self.metadata['texts'][i],
                "path": os.path.join(self.root_dir, self.metadata['paths'][i]),  # 相对路径转绝对路径
                "raw_text": self.metadata['raw_texts'][i].replace('_', '')
            } for i in sorted_indices]
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []

class ImageSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("字幕截图搜索系统")
        self.root.geometry(CONFIG['layout']['window_size'])
        
        # 加载自定义字体
        self.custom_font = self.load_custom_font()
        
        # 高DPI适配
        if 'win' in self.root.tk.call('tk', 'windowingsystem'):
            self.root.tk.call('tk', 'scaling', 2.0)
        
        self.searcher = SubtitleSearcher()
        self.current_images = []
        self.setup_ui()
        
        # 自动搜索
        self.root.after(100, self.auto_search)

    def load_custom_font(self):
        """加载并注册自定义字体"""
        try:
            font_prop = FontProperties(fname=CUSTOM_FONT_PATH)
            fontManager.addfont(CUSTOM_FONT_PATH)
            font_name = font_prop.get_name()
            tk_font = font.Font(family=font_name, size=10)
            self.root.option_add("*Font", tk_font)
            print(f"✅ 已加载字体: {font_name}")
            return font_name
        except Exception as e:
            print(f"❌ 字体加载失败: {str(e)}")
            return CONFIG['font']['fallback']

    def setup_ui(self):
        # 搜索框区域
        search_frame = ttk.Frame(self.root)
        search_frame.pack(pady=20, fill=tk.X, padx=30)
        
        self.entry = ttk.Entry(
            search_frame, 
            font=(self.custom_font, CONFIG['font']['sizes']['entry']),
            width=CONFIG['layout']['entry_width']
        )
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        self.entry.bind('<Return>', lambda event: self.on_search())
        
        search_btn = ttk.Button(
            search_frame, 
            text="搜索", 
            command=self.on_search,
            style='Accent.TButton',
            width=CONFIG['layout']['button']['width']
        )
        search_btn.pack(side=tk.LEFT, padx=10)

        # 结果显示区域
        self.results_frame = ttk.Frame(self.root)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # 配置网格布局
        for row in range(2):
            self.results_frame.rowconfigure(row, weight=1)
        for col in range(3):
            self.results_frame.columnconfigure(col, weight=1, uniform='col')

        # 初始化6个结果容器
        self.result_slots = []
        for row in range(2):
            for col in range(3):
                container = ttk.Frame(self.results_frame)
                container.grid(row=row, column=col, sticky=tk.NSEW, padx=15, pady=15)
                
                # 图片显示区域
                canvas = tk.Canvas(
                    container, 
                    width=CONFIG['layout']['image']['width'],
                    height=CONFIG['layout']['image']['height'],
                    bg=CONFIG['colors']['background']
                )
                canvas.pack(pady=5)
                
                # 元信息显示
                meta_frame = ttk.Frame(container)
                meta_frame.pack(fill=tk.X)
                
                # 相似度标签
                score_label = ttk.Label(
                    meta_frame, 
                    foreground=CONFIG['font']['colors']['score'],
                    font=(self.custom_font, CONFIG['font']['sizes']['score'], 'bold'),
                    anchor='center'
                )
                score_label.pack(fill=tk.X, pady=2)
                
                # 原始文本标签
                text_label = ttk.Label(
                    meta_frame,
                    wraplength=CONFIG['layout']['wraplength'],
                    foreground=CONFIG['font']['colors']['text'],
                    font=(self.custom_font, CONFIG['font']['sizes']['text']),
                    anchor='center'
                )
                text_label.pack(fill=tk.X, pady=2)
                
                # 复制按钮
                copy_btn = ttk.Button(
                    container,
                    text="复制到剪贴板",
                    command=lambda p=None: self.copy_image(p),
                    style='Primary.TButton',
                    width=CONFIG['layout']['button']['width']
                )
                copy_btn.pack(pady=5, fill=tk.X)
                
                self.result_slots.append({
                    "canvas": canvas,
                    "score": score_label,
                    "text": text_label,
                    "button": copy_btn
                })

        # 样式配置
        style = ttk.Style()
        style.configure('Accent.TButton', 
                       font=(self.custom_font, CONFIG['font']['sizes']['search_button']),
                       foreground=CONFIG['font']['colors']['button_text'],
                       background=CONFIG['colors']['button']['search'])
        style.configure('Primary.TButton', 
                       font=(self.custom_font, CONFIG['font']['sizes']['button']),
                       foreground=CONFIG['font']['colors']['button_text'],
                       background=CONFIG['colors']['button']['copy'])

    def auto_search(self):
        """自动执行初始搜索"""
        self.entry.insert(0, "为什么要演奏春日影")
        self.on_search()

    def on_search(self):
        """执行搜索并清空搜索框"""
        query = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        
        if not query:
            messagebox.showwarning("提示", "请输入搜索内容")
            return
        
        try:
            results = self.searcher.search(query)
            self.display_results(results)
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {str(e)}")

    def display_results(self, results):
        # 清空当前显示
        for slot in self.result_slots:
            slot["canvas"].delete("all")
            slot["score"].config(text="")
            slot["text"].config(text="")
            slot["button"].config(state=tk.DISABLED, command=lambda: None)
        
        self.current_images.clear()
        
        # 加载新结果
        for i, result in enumerate(results[:6]):
            try:
                img = Image.open(result["path"])
                img.thumbnail((CONFIG['layout']['image']['width'], CONFIG['layout']['image']['height']))
                tk_img = ImageTk.PhotoImage(img)
                
                slot = self.result_slots[i]
                slot["canvas"].create_image(
                    CONFIG['layout']['image']['width']//2,
                    CONFIG['layout']['image']['height']//2,
                    image=tk_img
                )
                slot["score"].config(text=f"相似度: {result['score']:.2f}")
                slot["text"].config(text=result["raw_text"])
                slot["button"].config(
                    state=tk.NORMAL,
                    command=lambda p=result["path"]: self.copy_image(p)
                )
                
                self.current_images.append(tk_img)
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {result['path']}\n{str(e)}")

    def copy_image(self, path):
        try:
            img = Image.open(path)
            output = io.BytesIO()
            img.save(output, format="BMP")
            data = output.getvalue()[14:]
            output.close()
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            messagebox.showinfo("成功", "图片已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")

if __name__ == "__main__":
    # 检查并预处理
    if not check_and_preprocess():
        print("❌ 预处理失败，无法启动 GUI")
        exit(1)

    # 启动 GUI
    root = tk.Tk()
    
    if 'win' in root.tk.call('tk', 'windowingsystem'):
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    app = ImageSearchApp(root)
    root.mainloop()