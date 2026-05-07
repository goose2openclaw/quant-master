#!/usr/bin/env python3
"""
处理新音频文件
"""

import os
import sys
import json
import time
from pathlib import Path

def transcribe_audio(audio_path, model_size="tiny", language="zh"):
    """使用faster-whisper转录音频"""
    from faster_whisper import WhisperModel
    
    print(f"🎙️ 开始转录: {os.path.basename(audio_path)}")
    print(f"   模型: {model_size}, 语言: {language}")
    
    start_time = time.time()
    
    try:
        # 加载模型
        print("📦 加载模型...")
        model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root="./models"
        )
        
        # 转录音频
        print("🔊 处理音频...")
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True
        )
        
        # 收集结果
        full_text = ""
        segments_list = []
        
        for segment in segments:
            segment_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            segments_list.append(segment_data)
            full_text += segment.text + " "
        
        processing_time = time.time() - start_time
        
        result = {
            "success": True,
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "processing_time": processing_time,
            "segments": segments_list,
            "model": model_size
        }
        
        print(f"✅ 转录完成! 耗时: {processing_time:.2f}秒")
        print(f"   检测语言: {info.language} (概率: {info.language_probability:.2%})")
        print(f"   音频时长: {info.duration:.2f}秒")
        print(f"   文本长度: {len(full_text)}字符")
        
        return result
        
    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def save_results(result, audio_path, output_dir="transcriptions"):
    """保存转录结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # 保存JSON
    json_path = os.path.join(output_dir, f"{base_name}_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"📄 JSON保存到: {json_path}")
    
    # 保存文本
    if result["success"]:
        txt_path = os.path.join(output_dir, f"{base_name}_{timestamp}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"📝 文本保存到: {txt_path}")
        
        # 保存带时间戳的文本
        segments_path = os.path.join(output_dir, f"{base_name}_{timestamp}_segments.txt")
        with open(segments_path, "w", encoding="utf-8") as f:
            for segment in result["segments"]:
                f.write(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}\n")
        print(f"⏱️  时间戳文本保存到: {segments_path}")
    
    return {
        "json": json_path,
        "text": txt_path if result["success"] else None,
        "segments": segments_path if result["success"] else None
    }

def main():
    """主函数"""
    print("🎵 处理新音频文件")
    print("="*50)
    
    # 新音频文件
    new_audio = "/home/goose/.openclaw/media/inbound/file_2---3e3091eb-2d94-4c0c-b0ad-6392e5bc9533.ogg"
    
    # 检查文件
    if not os.path.exists(new_audio):
        print(f"❌ 文件不存在: {new_audio}")
        
        # 列出所有音频文件
        audio_dir = "/home/goose/.openclaw/media/inbound"
        print(f"\n📁 音频目录内容:")
        files = os.listdir(audio_dir)
        for file in files:
            if file.endswith(('.ogg', '.mp3', '.wav')):
                file_path = os.path.join(audio_dir, file)
                size = os.path.getsize(file_path)
                print(f"  - {file} ({size/1024:.1f} KB)")
        
        return
    
    # 文件信息
    size = os.path.getsize(new_audio)
    print(f"📄 文件: {os.path.basename(new_audio)}")
    print(f"📏 大小: {size/1024:.1f} KB")
    print(f"🕒 修改时间: {time.ctime(os.path.getmtime(new_audio))}")
    
    # 转录
    print(f"\n{'='*60}")
    print("开始转录...")
    print(f"{'='*60}")
    
    result = transcribe_audio(new_audio, model_size="tiny", language="zh")
    
    # 保存结果
    if result["success"]:
        files = save_results(result, new_audio)
        
        # 显示预览
        print("\n🔍 转录内容:")
        print("="*50)
        print(result["text"])
        print("="*50)
        
        # 归档文件
        print("\n📦 归档文件...")
        archive_dir = "/home/goose/.openclaw/workspace/audio_archive"
        os.makedirs(archive_dir, exist_ok=True)
        
        archive_path = os.path.join(archive_dir, os.path.basename(new_audio))
        import shutil
        shutil.copy2(new_audio, archive_path)
        print(f"✅ 文件已归档到: {archive_path}")
        
        # 更新记忆
        print("\n📝 更新记忆文件...")
        memory_entry = f"""
### 上午 (11:52) - 新音频处理
- **文件**: {os.path.basename(new_audio)}
- **内容**: "{result['text']}"
- **时长**: {result['duration']:.2f}秒
- **处理时间**: {result['processing_time']:.2f}秒
- **语言**: {result['language']} ({result['language_probability']:.2%})
- **输出文件**: {os.path.basename(files['text'])}
"""
        
        print("✅ 处理完成!")
        print(f"\n📋 总结:")
        print(f"  内容: {result['text']}")
        print(f"  文件: {os.path.basename(files['text'])}")
        print(f"  归档: {archive_path}")
        
    else:
        print(f"❌ 处理失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()