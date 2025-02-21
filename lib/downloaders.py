import logging
import os
import subprocess
import traceback
import time
import requests
import instaloader
import yt_dlp
from typing import Optional

logger = logging.getLogger(__name__)

async def download_youtube_video(url: str, quality: str) -> Optional[str]:
    try:
        file_path = f"/tmp/youtube_video_{int(time.time())}.mp4"
        height = quality[:-1]
        
        ydl_opts = {
            'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best[ext=mp4]',
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'no_check_certificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists(file_path):
            logger.info(f"Vídeo baixado com sucesso: {file_path}")
            return file_path
            
        logger.error("Arquivo não foi criado após o download")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao baixar vídeo do YouTube: {str(e)}\nTraceback: {traceback.format_exc()}")
        return None

async def download_instagram_video(url: str, quality: str) -> Optional[str]:
    try:
        L = instaloader.Instaloader()
        post = instaloader.Post.from_url(L.context, url)
        video_url = post.video_url
        if not video_url:
            return None
            
        response = requests.get(video_url, stream=True)
        file_path = f"/tmp/instagram_video_{quality}.mp4"
        with open(file_path, "wb") as video_file:
            for chunk in response.iter_content(chunk_size=8192):
                video_file.write(chunk)
        return file_path
    except Exception as e:
        logger.error(f"Erro ao baixar vídeo do Instagram: {e}")
        return None

async def download_tiktok_video(url: str, quality: str) -> Optional[str]:
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
            
        file_path = f"/tmp/tiktok_video_{quality}.mp4"
        with open(file_path, "wb") as video_file:
            video_file.write(response.content)
        return file_path
    except Exception as e:
        logger.error(f"Erro ao baixar vídeo do TikTok: {e}")
        return None
