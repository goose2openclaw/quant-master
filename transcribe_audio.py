#!/usr/bin/env python3
import speech_recognition as sr
import os
import sys

def transcribe_audio(audio_path):
    """转录音频文件为文本"""
    try:
        # 初始化识别器
        recognizer = sr.Recognizer()
        
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            print(f"错误: 文件不存在: {audio_path}")
            return None
            
        print(f"处理音频文件: {audio_path}")
        print(f"文件大小: {os.path.getsize(audio_path)} 字节")
        
        # 使用AudioFile加载音频
        with sr.AudioFile(audio_path) as source:
            print("读取音频数据...")
            audio_data = recognizer.record(source)
            
            print("开始语音识别...")
            # 尝试使用Google Web Speech API（免费）
            try:
                text = recognizer.recognize_google(audio_data, language='zh-CN')
                print("✅ 识别成功 (Google Web Speech API)")
                return text
            except sr.UnknownValueError:
                print("❌ Google Web Speech API 无法理解音频")
                return None
            except sr.RequestError as e:
                print(f"❌ Google Web Speech API 请求错误: {e}")
                
                # 尝试使用Sphinx（离线）
                try:
                    print("尝试使用CMU Sphinx (离线)...")
                    text = recognizer.recognize_sphinx(audio_data, language='zh-CN')
                    print("✅ 识别成功 (CMU Sphinx)")
                    return text
                except sr.UnknownValueError:
                    print("❌ CMU Sphinx 无法理解音频")
                    return None
                except Exception as e:
                    print(f"❌ CMU Sphinx 错误: {e}")
                    return None
                    
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 transcribe_audio.py <音频文件路径>")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    result = transcribe_audio(audio_file)
    
    if result:
        print("\n" + "="*50)
        print("📝 转录结果:")
        print("="*50)
        print(result)
        print("="*50)
        
        # 保存结果到文件
        output_file = audio_file + ".txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"\n✅ 结果已保存到: {output_file}")
    else:
        print("\n❌ 无法转录音频文件")