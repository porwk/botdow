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
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',  # Arquivo de cookies se necessário
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'socket_timeout': 30,
            'retries': 3,
        }
        
        for attempt in range(3):  # Tenta 3 vezes
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Tentativa {attempt + 1} de download do YouTube")
                    ydl.download([url])
                    
                if os.path.exists(file_path):
                    logger.info(f"Vídeo baixado com sucesso: {file_path}")
                    return file_path
                    
            except yt_dlp.utils.DownloadError as e:
                if attempt < 2:  # Se não for a última tentativa
                    logger.warning(f"Tentativa {attempt + 1} falhou, tentando novamente...")
                    time.sleep(2)  # Espera 2 segundos antes de tentar novamente
                else:
                    raise  # Re-lança a exceção na última tentativa
        
        logger.error("Arquivo não foi criado após todas as tentativas")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao baixar vídeo do YouTube: {str(e)}\nTraceback: {traceback.format_exc()}")
        return None

async def _download_instagram_video_internal(url: str, quality: str) -> Optional[str]:
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

def download_instagram_video(url: str, quality: str = None) -> None:
    raise DeprecationWarning("Use download_video('instagram', url, quality) instead")
