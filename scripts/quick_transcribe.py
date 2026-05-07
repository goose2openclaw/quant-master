#!/usr/bin/env python3
"""
快速音频转录脚本
在依赖安装完成后使用
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    deps = {
        "ffmpeg": False,
        "whisper": False,
        "python": False
    }
    
    # 检查ffmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            deps["ffmpeg"] = True
            print("✅ ffmpeg: 可用")
    except FileNotFoundError:
        print("❌ ffmpeg: 未找到")
    
    # 检查python
    try:
        import whisper
        deps["whisper"] = True
        print("✅ whisper: 已安装")
    except ImportError:
        print("❌ whisper: 未安装")
    
    # 检查所有依赖
    if all(deps.values()):
        print("🎉 所有依赖已就绪!")
        return True
    else:
        print("⚠ 缺少依赖，无法继续")
        return False

def get_audio_info(audio_path):
    """获取音频文件信息"""
    print(f"📁 音频文件: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"❌ 文件不存在: {audio_path}")
        return None
    
    # 基本信息
    size = os.path.getsize(audio_path)
    size_mb = size / (1024 * 1024)
    
    print(f"📏 文件大小: {size_mb:.2f} MB ({size} 字节)")
    
    # 使用ffmpeg获取详细信息
    try:
        cmd = ["ffmpeg", "-i", audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
        
        # 提取信息
        for line in result.stdout.split('\n'):
            if "Duration" in line:
                print(f"⏱️  时长: {line.strip()}")
            elif "Audio:" in line:
                print(f"🎵 音频信息: {line.strip()}")
            elif "Stream" in line and "Audio" in line:
                print(f"🔊 流信息: {line.strip()}")
                
    except Exception as e:
        print(f"⚠ 无法获取详细音频信息: {e}")
    
    return {
        "path": audio_path,
        "size": size,
        "size_mb": size_mb
    }

def transcribe_with_whisper(audio_path, output_dir="transcriptions"):
    """使用whisper转录音频"""
    import whisper
    
    print(f"\n🎙️ 开始转录: {os.path.basename(audio_path)}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载模型（使用较小的模型以加快速度）
    print("📦 加载模型...")
    try:
        model = whisper.load_model("base")  # 使用base模型，较小较快
    except Exception as e:
        print(f"❌ 加载模型失败: {e}")
        print("尝试使用tiny模型...")
        model = whisper.load_model("tiny")
    
    # 转录音频
    print("🔊 处理音频...")
    try:
        result = model.transcribe(
            audio_path,
            language="zh",  # 假设是中文
            task="transcribe",
            temperature=0.0,
            best_of=5,
            beam_size=5
        )
        
        print("✅ 转录完成!")
        
        # 保存结果
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_files = []
        
        # 1. 保存JSON
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        output_files.append(json_path)
        print(f"📄 JSON保存到: {json_path}")
        
        # 2. 保存文本
        txt_path = os.path.join(output_dir, f"{base_name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        output_files.append(txt_path)
        print(f"📝 文本保存到: {txt_path}")
        
        # 3. 显示预览
        print("\n🔍 转录预览:")
        print("="*50)
        text_preview = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
        print(text_preview)
        print("="*50)
        
        return {
            "success": True,
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "duration": result.get("duration", 0),
            "files": output_files
        }
        
    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """主函数"""
    print("🎵 快速音频转录工具")
    print("="*50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n🚨 请先安装依赖:")
        print("1. FFmpeg: sudo apt install ffmpeg")
        print("2. Whisper: pip install openai-whisper")
        return
    
    # 音频文件路径
    audio_files = [
        "/home/goose/.openclaw/media/inbound/file_0---da5d3e22-026b-4307-9040-7fce951a44be.ogg",
        "/home/goose/.openclaw/media/inbound/file_1---759070ed-d58c-4f44-a310-0c55f12a7695.ogg"
    ]
    
    print(f"\n📋 找到 {len(audio_files)} 个音频文件")
    
    # 处理每个文件
    for i, audio_path in enumerate(audio_files, 1):
        print(f"\n{'='*60}")
        print(f"处理文件 {i}/{len(audio_files)}")
        print(f"{'='*60}")
        
        # 检查文件
        info = get_audio_info(audio_path)
        if not info:
            continue
        
        # 转录
        result = transcribe_with_whisper(audio_path)
        
        if result["success"]:
            print(f"\n✅ 文件处理完成:")
            print(f"   语言: {result['language']}")
            print(f"   时长: {result['duration']:.2f}秒")
            print(f"   文本长度: {len(result['text'])}字符")
            print(f"   输出文件: {len(result['files'])}个")
        else:
            print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")
    
    print(f"\n{'='*60}")
    print("🎉 所有文件处理完成!")
    print("输出目录: transcriptions/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()