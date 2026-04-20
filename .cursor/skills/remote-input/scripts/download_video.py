#!/usr/bin/env python3
"""
Video Downloader (YouTube & Bilibili)
Downloads videos from YouTube and Bilibili with customizable quality and format options.
"""

import argparse
import os
import subprocess
import json
import re
import time
from pathlib import Path


def is_youtube_url(url: str) -> bool:
    """Check if the URL is a valid YouTube URL."""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
    ]
    return any(re.match(p, url.strip()) for p in patterns)


def is_bilibili_url(url: str) -> bool:
    """Check if the URL is a valid Bilibili URL."""
    patterns = [
        r'(?:https?://)?(?:www\.)?bilibili\.com/video/[Bb][Vv][\w]+',
        r'(?:https?://)?(?:www\.)?bilibili\.com/video/av\d+',
        r'(?:https?://)?(?:www\.)?bilibili\.com/av\d+',
        r'(?:https?://)?b23\.tv/[\w]+',
    ]
    return any(re.match(p, url.strip()) for p in patterns)


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/)([\w-]+)',
        r'youtu\.be/([\w-]+)',
        r'youtube\.com/shorts/([\w-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def extract_bilibili_id(url: str) -> str:
    """Extract video ID from Bilibili URL formats."""
    # BV号格式: bilibili.com/video/BV1xx411c7JZ
    bv_match = re.search(r'(?:bilibili\.com/video/)([Bb][Vv][\w]+)', url)
    if bv_match:
        return bv_match.group(1)
    
    # AV号格式: bilibili.com/video/av12345678 或 bilibili.com/av12345678
    av_match = re.search(r'(?:bilibili\.com/(?:video/)?)(av\d+)', url, re.IGNORECASE)
    if av_match:
        return av_match.group(1).lower()
    
    # B23短链: b23.tv/abc123
    b23_match = re.search(r'b23\.tv/([\w]+)', url)
    if b23_match:
        return b23_match.group(1)
    
    return ""


def check_yt_dlp():
    """Check if yt-dlp is installed, install if not."""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("yt-dlp not found. Installing...")
        subprocess.run([os.sys.executable, "-m", "pip", "install", "--break-system-packages", "yt-dlp"], check=True)


def get_video_info(url):
    """Get information about the video without downloading."""
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-playlist", url],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)


def detect_video_source(url: str) -> str:
    """
    Detect video source type from URL.
    
    Returns:
        'youtube' - YouTube URL
        'bilibili' - Bilibili URL
        'unknown' - Not a supported URL
    """
    if is_youtube_url(url):
        return "youtube"
    elif is_bilibili_url(url):
        return "bilibili"
    return "unknown"


def check_media_has_audio(file_path: str) -> bool:
    """
    使用 ffprobe 检查视频文件是否包含音频轨道。
    
    Args:
        file_path: 媒体文件路径
    
    Returns:
        True 如果有音频轨道，False 否则
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=index",
                "-of", "json",
                file_path
            ],
            capture_output=True,
            text=True,
            check=False
        )
        # 如果有音频流，输出中会包含 "streams"
        return "streams" in result.stdout and "index" in result.stdout
    except FileNotFoundError:
        # ffprobe 不可用，尝试用 ffmpeg 检查
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", file_path],
                capture_output=True,
                text=True
            )
            output = result.stderr + result.stdout
            return "Audio:" in output or "audio" in output.lower()
        except:
            return True  # 无法检测，假设有音频
    except Exception:
        return True  # 出错时假设有音频


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    使用 ffmpeg 合并视频和音频文件。
    
    Args:
        video_path: 视频文件路径
        audio_path: 音频文件路径
        output_path: 输出文件路径
    
    Returns:
        True 如果合并成功，False 否则
    """
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",  # 保持视频编码不变
                "-c:a", "aac",   # 音频转 AAC
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",     # 以短的那个为准
                output_path
            ],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def download_video(url, output_path="/mnt/user-data/outputs", quality="best", 
                   format_type="mp4", audio_only=False, download_subtitle=False):
    """
    Download a video from YouTube or Bilibili.
    
    Args:
        url: Video URL (YouTube or Bilibili)
        output_path: Directory to save the video
        quality: Quality setting (best, 1080p, 720p, 480p, 360p, worst)
        format_type: Output format (mp4, webm, mkv, etc.)
        audio_only: Download only audio (mp3)
        download_subtitle: For Bilibili, download subtitles if available
    
    Returns:
        dict with keys: success (bool), path (str), title (str), video_id (str), 
                       source (str), audio_path (str), merge_failed (bool)
    """
    check_yt_dlp()
    
    # 检测视频来源
    source = detect_video_source(url)
    if source == "unknown":
        return {
            "success": False,
            "path": None,
            "title": "",
            "video_id": "",
            "source": "unknown",
            "error": "Unsupported URL. Supported: YouTube, Bilibili"
        }
    
    # 根据来源设置 video_id
    if source == "youtube":
        video_id = extract_video_id(url)
    else:
        video_id = extract_bilibili_id(url)
    
    title = ""
    
    # 构建 yt-dlp 命令
    cmd = ["yt-dlp"]
    
    if audio_only:
        cmd.extend([
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ])
    else:
        # 视频质量设置
        if quality == "best":
            format_string = "bestvideo+bestaudio/best"
        elif quality == "worst":
            format_string = "worstvideo+worstaudio/worst"
        else:
            height = quality.replace("p", "")
            format_string = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        
        cmd.extend([
            "-f", format_string,
            "--merge-output-format", format_type,
        ])
    
    # Bilibili 特殊参数
    if source == "bilibili":
        # B 站需要登录才能下载，添加必要的头部
        cmd.extend([
            "--add-header", "Referer:https://www.bilibili.com",
        ])
        if download_subtitle:
            cmd.extend(["--write-subs", "--write-auto-subs", "--sub-lang", "zh-CN,zh-Hans"])
    
    # 输出模板
    output_template = f"{output_path}/%(title)s.%(ext)s"
    cmd.extend([
        "-o", output_template,
        "--no-playlist",
        "--quiet",
    ])
    
    cmd.append(url)
    
    try:
        # 获取视频信息
        info = get_video_info(url)
        title = info.get('title', 'Unknown')
        duration = int(info.get('duration', 0) or 0)
        uploader = info.get('uploader', 'Unknown')
        
        # 根据来源显示不同的提示信息
        if source == "youtube":
            source_name = "YouTube"
        else:
            source_name = "Bilibili"
        
        print(f"Downloading {source_name} video:")
        print(f"  Title: {title}")
        print(f"  Video ID: {video_id}")
        print(f"  Duration: {duration // 60}:{duration % 60:02d}")
        print(f"  Uploader: {uploader}")
        print(f"  Quality: {quality}")
        print(f"  Format: {'mp3 (audio only)' if audio_only else format_type}")
        print(f"  Output: {output_path}")
        
        # 下载视频
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # 收集所有下载的文件
        downloaded_files = []
        for f in os.listdir(output_path):
            if not f.startswith('.'):
                full_path = os.path.join(output_path, f)
                downloaded_files.append((f, full_path))
        
        # 按修改时间排序
        downloaded_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
        
        # 默认值
        downloaded_path = None
        audio_path = None
        merge_failed = False
        available_audio_files = []
        
        if downloaded_files:
            # 分离视频和音频文件
            video_files = []
            pure_audio_files = []
            for fname, fpath in downloaded_files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in ['.mp4', '.mkv', '.webm', '.avi', '.mov']:
                    video_files.append((fname, fpath))
                elif ext in ['.mp3', '.m4a', '.wav', '.aac', '.ogg', '.webm']:
                    pure_audio_files.append((fname, fpath))
            
            # 检查合并是否成功（最新的视频文件是否有音频）
            if video_files:
                main_video = video_files[0]
                if not check_media_has_audio(main_video[1]):
                    print(f"\n[WARNING] 主视频文件 {main_video[0]} 没有音频轨道，尝试合并...")
                    merge_failed = True
                    
                    # 查找可能的音频文件（包含 .f 模式的 .webm 文件通常是音频）
                    for fname, fpath in downloaded_files[1:]:
                        if '.f' in fname and os.path.splitext(fname)[1].lower() == '.webm':
                            if check_media_has_audio(fpath):
                                pure_audio_files.append((fname, fpath))
                    
                    # 尝试用已有的音频文件合并
                    merged_success = False
                    if pure_audio_files:
                        audio_file = pure_audio_files[0]
                        merged_output = main_video[1]
                        merged_success = merge_audio_video(main_video[1], audio_file[1], merged_output)
                        
                        if merged_success:
                            print(f"[OK] 已成功合并音频: {audio_file[0]} -> {main_video[0]}")
                            audio_path = audio_file[1]
                            merge_failed = False
                        else:
                            print(f"[WARNING] 合并失败，将使用纯音频文件代替")
                            audio_path = audio_file[1]
                    else:
                        print(f"[WARNING] 没有找到可用的音频文件进行合并")
                        audio_path = None
                else:
                    audio_path = None
            
            # 设置主文件路径
            if video_files:
                downloaded_path = video_files[0][1]
        
        print(f"\nDownload complete: {downloaded_path}")
        
        # 写入元数据文件
        metadata_dir = Path(output_path) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        if source == "youtube":
            metadata_id = f"youtube_{video_id}"
        elif source == "bilibili":
            metadata_id = f"bilibili_{video_id}"
        else:
            metadata_id = f"{source}_{video_id}"
        
        metadata = {
            "ground_id": metadata_id,
            "source_type": source,
            "source_url": url,
            "downloaded_path": downloaded_path,
            "audio_path": audio_path,
            "merge_failed": merge_failed,
            "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": {
                "title": title,
                "video_id": video_id,
                "duration": duration,
                "uploader": uploader
            }
        }
        
        metadata_file = metadata_dir / f"{metadata_id}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] Metadata saved to: {metadata_file}")
        
        return {
            "success": True,
            "path": downloaded_path,
            "title": title,
            "video_id": video_id,
            "source": source,
            "duration": duration,
            "uploader": uploader,
            "audio_path": audio_path,
            "merge_failed": merge_failed
        }
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        print(f"stderr: {e.stderr}")
        return {
            "success": False,
            "path": None,
            "title": title,
            "video_id": video_id,
            "source": source,
            "audio_path": None,
            "merge_failed": False,
            "error": str(e)
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "success": False,
            "path": None,
            "title": title,
            "video_id": video_id,
            "source": source,
            "audio_path": None,
            "merge_failed": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Download videos from YouTube or Bilibili with customizable quality and format"
    )
    parser.add_argument("url", help="Video URL (YouTube or Bilibili)")
    parser.add_argument(
        "-o", "--output",
        default="/mnt/user-data/outputs",
        help="Output directory (default: /mnt/user-data/outputs)"
    )
    parser.add_argument(
        "-q", "--quality",
        default="best",
        choices=["best", "1080p", "720p", "480p", "360p", "worst"],
        help="Video quality (default: best)"
    )
    parser.add_argument(
        "-f", "--format",
        default="mp4",
        choices=["mp4", "webm", "mkv"],
        help="Video format (default: mp4)"
    )
    parser.add_argument(
        "-a", "--audio-only",
        action="store_true",
        help="Download only audio as MP3"
    )
    parser.add_argument(
        "-s", "--subtitle",
        action="store_true",
        help="Download subtitles (for Bilibili only)"
    )
    
    args = parser.parse_args()
    
    result = download_video(
        url=args.url,
        output_path=args.output,
        quality=args.quality,
        format_type=args.format,
        audio_only=args.audio_only,
        download_subtitle=args.subtitle
    )
    
    # Output JSON result for programmatic use
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    os.sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()