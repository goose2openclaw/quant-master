#!/usr/bin/env python3
"""
双语音频转录脚本
支持中文转录和英文翻译
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    # 检查ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ ffmpeg 已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg 未安装")
        print("请安装: sudo apt install ffmpeg 或 brew install ffmpeg")
        return False
    
    # 检查whisper
    try:
        import whisper
        print("✅ whisper 已安装")
    except ImportError:
        print("❌ whisper 未安装")
        print("请安装: pip install openai-whisper")
        return False
    
    return True

def transcribe_audio(audio_path, language="zh", task="transcribe", model="turbo"):
    """使用whisper转录音频"""
    import whisper
    
    print(f"🎙️ 开始转录: {audio_path}")
    print(f"  语言: {language}, 任务: {task}, 模型: {model}")
    
    try:
        # 加载模型
        print("📦 加载模型...")
        model_obj = whisper.load_model(model)
        
        # 转录音频
        print("🔊 处理音频...")
        result = model_obj.transcribe(
            audio_path,
            language=language,
            task=task,
            temperature=0.0
        )
        
        return result
        
    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return None

def save_results(result, output_dir, prefix):
    """保存转录结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存完整JSON
    json_path = os.path.join(output_dir, f"{prefix}_full.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"📄 完整结果保存到: {json_path}")
    
    # 保存纯文本
    txt_path = os.path.join(output_dir, f"{prefix}_text.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])
    print(f"📝 文本保存到: {txt_path}")
    
    # 保存带时间戳的文本
    if "segments" in result:
        segments_path = os.path.join(output_dir, f"{prefix}_segments.txt")
        with open(segments_path, "w", encoding="utf-8") as f:
            for segment in result["segments"]:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                f.write(f"[{start:.2f}s - {end:.2f}s] {text}\n")
        print(f"⏱️ 时间戳文本保存到: {segments_path}")
    
    return {
        "json": json_path,
        "text": txt_path,
        "segments": segments_path if "segments" in result else None
    }

def create_bilingual_report(chinese_result, english_result, output_dir):
    """创建双语报告"""
    report_path = os.path.join(output_dir, "bilingual_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 双语音频转录报告\n\n")
        f.write(f"音频文件: {audio_path}\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 中文转录\n")
        f.write("```\n")
        f.write(chinese_result["text"] + "\n")
        f.write("```\n\n")
        
        f.write("## 英文翻译\n")
        f.write("```\n")
        f.write(english_result["text"] + "\n")
        f.write("```\n\n")
        
        f.write("## 详细信息\n")
        f.write(f"- 检测语言: {chinese_result.get('language', '未知')}\n")
        f.write(f"- 音频时长: {chinese_result.get('duration', '未知')}秒\n")
        f.write(f"- 模型: turbo\n")
        f.write(f"- 任务: 转录 + 翻译\n")
    
    print(f"📊 双语报告保存到: {report_path}")
    return report_path

def main():
    """主函数"""
    import datetime
    
    # 音频文件路径
    audio_path = "/home/goose/.openclaw/media/inbound/file_0---da5d3e22-026b-4307-9040-7fce951a44be.ogg"
    
    if not os.path.exists(audio_path):
        print(f"❌ 音频文件不存在: {audio_path}")
        print("请检查文件路径")
        return
    
    print(f"🎵 音频文件: {audio_path}")
    print(f"📁 文件大小: {os.path.getsize(audio_path) / 1024:.2f} KB")
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 创建输出目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(audio_path), f"transcription_{timestamp}")
    
    print(f"\n📂 输出目录: {output_dir}")
    
    # 步骤1: 中文转录
    print("\n" + "="*50)
    print("🇨🇳 步骤1: 中文转录")
    print("="*50)
    
    chinese_result = transcribe_audio(
        audio_path,
        language="zh",
        task="transcribe",
        model="turbo"
    )
    
    if not chinese_result:
        print("❌ 中文转录失败")
        return
    
    chinese_files = save_results(chinese_result, output_dir, "chinese")
    
    # 步骤2: 英文翻译
    print("\n" + "="*50)
    print("🇺🇸 步骤2: 英文翻译")
    print("="*50)
    
    english_result = transcribe_audio(
        audio_path,
        language="zh",  # 源语言是中文
        task="translate",  # 翻译为英文
        model="turbo"
    )
    
    if not english_result:
        print("❌ 英文翻译失败")
        return
    
    english_files = save_results(english_result, output_dir, "english")
    
    # 步骤3: 创建双语报告
    print("\n" + "="*50)
    print("🌐 步骤3: 创建双语报告")
    print("="*50)
    
    report_path = create_bilingual_report(chinese_result, english_result, output_dir)
    
    # 完成
    print("\n" + "="*50)
    print("🎉 双语转录完成!")
    print("="*50)
    print(f"\n📋 生成的文件:")
    print(f"  中文转录: {chinese_files['text']}")
    print(f"  英文翻译: {english_files['text']}")
    print(f"  完整报告: {report_path}")
    print(f"\n📊 统计信息:")
    print(f"  中文文本长度: {len(chinese_result['text'])} 字符")
    print(f"  英文文本长度: {len(english_result['text'])} 字符")
    print(f"  检测语言: {chinese_result.get('language', '未知')}")
    print(f"  音频时长: {chinese_result.get('duration', '未知')}秒")
    
    # 显示预览
    print("\n🔍 预览:")
    print("\n中文转录 (前200字符):")
    print(chinese_result['text'][:200] + "..." if len(chinese_result['text']) > 200 else chinese_result['text'])
    
    print("\n英文翻译 (前200字符):")
    print(english_result['text'][:200] + "..." if len(english_result['text']) > 200 else english_result['text'])

if __name__ == "__main__":
    main()