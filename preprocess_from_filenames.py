import os
import re
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from zhconv import convert

def extract_text_from_filename(filename):
    """增强版文件名解析函数"""
    try:
        # 移除扩展名和序号
        base_name = Path(filename).stem
        
        # 处理带序号的文件名（兼容多种分隔符）
        if '_' in base_name or '-' in base_name:
            separators = ['_', '-']
            for sep in separators:
                parts = base_name.split(sep, 1)
                if parts[0].isdigit() and len(parts[0]) == 4:  # 匹配0001格式
                    return parts[1].strip()
        return base_name
    except Exception as e:
        print(f"文件名解析失败：{filename} - {str(e)}")
        return ""

def preprocess_from_filenames(root_dir="pict"):
    """修复后的预处理函数"""
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    all_texts = []
    all_paths = []
    
    # 修复文件路径搜索方式
    root_path = Path(root_dir)
    
    # 获取所有图片文件（修复类型错误）
    png_files = list(root_path.glob("**/*.png"))
    jpg_files = list(root_path.glob("**/*.jpg"))
    gif_files = list(root_path.glob("**/*.gif"))
    image_files = png_files + jpg_files + gif_files
    
    print(f"发现 {len(image_files)} 张图片文件")
    
    # 添加主进度条
    with tqdm(total=len(image_files), desc="处理进度", unit="file") as pbar:
        for img_path in image_files:
            try:
                # 提取并清洗文本
                raw_text = extract_text_from_filename(img_path.name)
                if not raw_text:
                    pbar.update(1)
                    continue
                
                # 简繁转换（带异常处理）
                try:
                    simplified = convert(raw_text, 'zh-cn')
                except Exception as conv_e:
                    print(f"简繁转换失败：{raw_text} - {conv_e}")
                    simplified = raw_text
                
                # 额外清洗步骤
                cleaned = re.sub(r'[_\-]+', ' ', simplified).strip()
                if not cleaned:
                    pbar.update(1)
                    continue
                
                all_texts.append(cleaned)
                all_paths.append(str(img_path.relative_to(root_path)))  # 使用相对路径
                
                # 更新进度条
                pbar.set_postfix({"latest": cleaned[:10] + "..."})
                pbar.update(1)
                
            except Exception as e:
                print(f"处理文件失败：{img_path} - {str(e)}")
                pbar.update(1)

    # 添加向量生成进度条
    print("生成文本向量...")
    embeddings = model.encode(
        all_texts,
        show_progress_bar=True,
        batch_size=128,  # 优化批量处理
        convert_to_numpy=True
    )

    # 保存数据（带进度显示）
    print("保存数据...")
    with tqdm(total=2, desc="保存文件") as save_pbar:
        np.save("vectors.npy", embeddings)
        save_pbar.update(1)
        with open("metadata.json", "w", encoding="utf-8") as f:
            json.dump({
                "paths": all_paths,
                "texts": all_texts,
                "raw_texts": [extract_text_from_filename(Path(p).name) for p in all_paths]
            }, f, ensure_ascii=False, indent=2)
        save_pbar.update(1)

    print(f"\n✅ 预处理完成！有效数据：{len(all_texts)} 条")

if __name__ == "__main__":
    preprocess_from_filenames()