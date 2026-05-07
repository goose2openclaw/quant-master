#!/usr/bin/env python3
"""
使用faster-whisper转录音频
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
    print("🎵 faster-whisper音频转录工具")
    print("="*50)
    
    # 音频文件列表
    audio_files = [
        "/home/goose/.openclaw/media/inbound/file_0---da5d3e22-026b-4307-9040-7fce951a44be.ogg",
        "/home/goose/.openclaw/media/inbound/file_1---759070ed-d58c-4f44-a310-0c55f12a7695.ogg"
    ]
    
    # 检查文件
    valid_files = []
    for audio_path in audio_files:
        if os.path.exists(audio_path):
            size = os.path.getsize(audio_path)
            print(f"✅ {os.path.basename(audio_path)} - {size/1024:.1f} KB")
            valid_files.append(audio_path)
        else:
            print(f"❌ {os.path.basename(audio_path)} - 文件不存在")
    
    if not valid_files:
        print("❌ 没有可用的音频文件")
        return
    
    print(f"\n📋 找到 {len(valid_files)} 个音频文件")
    
    # 处理每个文件
    all_results = []
    
    for i, audio_path in enumerate(valid_files, 1):
        print(f"\n{'='*60}")
        print(f"处理文件 {i}/{len(valid_files)}: {os.path.basename(audio_path)}")
        print(f"{'='*60}")
        
        # 转录
        result = transcribe_audio(audio_path, model_size="tiny", language="zh")
        
        # 保存结果
        if result["success"]:
            files = save_results(result, audio_path)
            all_results.append({
                "file": os.path.basename(audio_path),
                "result": result,
                "output_files": files
            })
            
            # 显示预览
            print("\n🔍 转录预览:")
            print("="*50)
            preview = result["text"][:300] + "..." if len(result["text"]) > 300 else result["text"]
            print(preview)
            print("="*50)
        else:
            print(f"❌ 处理失败: {result.get('error', '未知错误')}")
    
    # 生成报告
    if all_results:
        print(f"\n{'='*60}")
        print("📊 处理报告")
        print(f"{'='*60}")
        
        total_chars = sum(len(r["result"]["text"]) for r in all_results)
        total_time = sum(r["result"]["processing_time"] for r in all_results)
        
        print(f"✅ 成功处理: {len(all_results)}/{len(valid_files)} 个文件")
        print(f"📝 总文本长度: {total_chars} 字符")
        print(f"⏱️  总处理时间: {total_time:.2f} 秒")
        print(f"📁 输出目录: transcriptions/")
        
        for r in all_results:
            print(f"\n  📄 {r['file']}:")
            print(f"    语言: {r['result']['language']}")
            print(f"    时长: {r['result']['duration']:.2f}秒")
            print(f"    处理时间: {r['result']['processing_time']:.2f}秒")
            print(f"    文本文件: {os.path.basename(r['output_files']['text'])}")
    
    print(f"\n{'='*60}")
    print("🎉 音频处理完成!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()