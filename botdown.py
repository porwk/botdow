import sys
import os
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

# Adiciona o diretório atual ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.downloaders import download_youtube_video, download_instagram_video, download_tiktok_video

# Configuração do logger
logger = logging.getLogger(__name__)

async def download_video(platform: str, url: str, quality: str) -> Optional[str]:
    PLATFORM_DOWNLOADERS = {
        "youtube": download_youtube_video,
        "instagram": download_instagram_video,
        "tiktok": download_tiktok_video
    }
    
    try:
        downloader = PLATFORM_DOWNLOADERS.get(platform)
        if downloader:
            return await downloader(url, VIDEO_QUALITIES[quality])
        return None
    except Exception as e:
        logger.error(f"Erro ao baixar vídeo: {e}")
        return None

async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = extract_url(update.message.text)
        if not url:
            await update.message.reply_text("Por favor, envie um link válido do YouTube.")
            return
            
        file_path = await download_video("youtube", url, "high")
        if file_path:
            await send_video(update, context, file_path)
        else:
            await update.message.reply_text("Não foi possível baixar o vídeo.")
    except Exception as e:
        logger.error(f"Erro ao processar vídeo do YouTube: {e}")
        await update.message.reply_text("Ocorreu um erro ao processar o vídeo.")

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = extract_url(update.message.text)
        logger.info(f"Processando URL do Instagram: {url}")
        
        if not url:
            await update.message.reply_text("Por favor, envie um link válido do Instagram.")
            return
        
        logger.info("Chamando download_video...")
        file_path = await download_video("instagram", url, "high")
        logger.info(f"Resultado do download: {file_path}")
        
        if file_path:
            await send_video(update, context, file_path)
        else:
            await update.message.reply_text("Não foi possível baixar o vídeo.")
    except Exception as e:
        logger.error(f"Erro ao processar vídeo do Instagram: {e}")
        logger.error(f"Traceback completo:", exc_info=True)
        await update.message.reply_text("Ocorreu um erro ao processar o vídeo.")

async def handle_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = extract_url(update.message.text)
        if not url:
            await update.message.reply_text("Por favor, envie um link válido do TikTok.")
            return
            
        file_path = await download_video("tiktok", url, "high")
        if file_path:
            await send_video(update, context, file_path)
        else:
            await update.message.reply_text("Não foi possível baixar o vídeo.")
    except Exception as e:
        logger.error(f"Erro ao processar vídeo do TikTok: {e}")
        await update.message.reply_text("Ocorreu um erro ao processar o vídeo.")