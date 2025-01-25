# MyGO_Chat
自动检索MyGO中与输入最相似的台词，日常聊天中再也不用自己讲话了（不是

## 使用方法

### 1. 环境准备

确保已安装以下依赖：

- Python 3.10

可以通过以下命令安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 文件结构

确保项目目录结构如下：

```
project/
├── pict/                  # 存放字幕截图的文件夹（支持子文件夹）
├── vectors.npy            # 图片向量文件（自动生成）
├── metadata.json          # 图片元数据文件（自动生成）
├── preprocess_from_filenames.py  # 预处理脚本
├── main.py                # 主程序
├── README.md              # 项目说明文件
└── requirements.txt       # 依赖库列表
```

### 3. 运行程序

1. 将额外表情包放入 `pict/extra` 文件夹中。
2. 运行主程序：

   ```bash
   python main.py
   ```

3. 在 GUI 中输入文本进行搜索，系统会显示最相关的字幕截图。

## 注意事项

1. **图片格式**：
   - 支持 `.png`, `.jpg`, `.jpeg`, `.gif` 格式的图片。

2. **预处理脚本**：
   - 如果 `pict` 文件夹中的图片数量较多，预处理可能需要较长时间。

3. **Windows 剪贴板支持**：
   - 复制图片功能仅支持 Windows 系统。如果需要在其他系统上运行，请移除或替换剪贴板相关代码。

## 示例

### 搜索界面
![image](https://github.com/user-attachments/assets/e8c43295-27ec-4388-b4bd-86aece85dd00)


## 未来改进

- 增加批量导入和导出功能。
- 优化预处理速度，支持增量更新。

## 贡献

欢迎提交 Issue 或 Pull Request 改进本项目！
