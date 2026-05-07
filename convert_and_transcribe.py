#!/usr/bin/env python3
import speech_recognition as sr
from pydub import AudioSegment
import os
import sys

def convert_ogg_to_wav(ogg_path, wav_path):
    """将OGG文件转换为WAV格式"""
    try:
        print(f"转换 {ogg_path} 到 {wav_path}...")
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        print(f"✅ 转换完成: {wav_path}")
        return True
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False

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
                # 尝试英文识别
                try:
                    print("尝试英文识别...")
                    text = recognizer.recognize_google(audio_data, language='en-US')
                    print("✅ 识别成功 (英文)")
                    return text
                except:
                    pass
                return None
            except sr.RequestError as e:
                print(f"❌ Google Web Speech API 请求错误: {e}")
                return None
                    
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 convert_and_transcribe.py <音频文件路径>")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    
    # 检查文件格式
    if audio_file.lower().endswith('.ogg'):
        # 转换为WAV
        wav_file = audio_file.replace('.ogg', '.wav')
        if convert_ogg_to_wav(audio_file, wav_file):
            audio_file = wav_file
        else:
            print("❌ 格式转换失败")
            sys.exit(1)
    
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
        
        # 清理临时WAV文件
        if wav_file and os.path.exists(wav_file):
            os.remove(wav_file)
            print(f"清理临时文件: {wav_file}")
    else:
        print("\n❌ 无法转录音频文件")
        
        # 提供备选方案
        print("\n🔧 备选方案:")
        print("1. 安装whisper命令行工具:")
        print("   brew install openai-whisper  # macOS")
        print("   pip install openai-whisper   # Python")
        print("2. 使用其他在线语音识别服务")
        print("3. 手动输入音频内容")