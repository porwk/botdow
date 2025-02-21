// ... existing code ...

# Remover as funções de download que foram movidas e substituir por:
from lib.downloaders import download_youtube_video, download_instagram_video, download_tiktok_video

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

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = extract_url(update.message.text)
        if not url:
            await update.message.reply_text("Por favor, envie um link válido do Instagram.")
            return
            
        # Corrigindo a chamada da função: adicionando await e o parâmetro quality
        file_path = await download_instagram_video(url, "high")  # Versão 1
        # OU
        # file_path = await download_video("instagram", url, "high")  # Versão 2 (recomendada)
        
        if file_path:
            await send_video(update, context, file_path)
        else:
            await update.message.reply_text("Não foi possível baixar o vídeo.")
    except Exception as e:
        logger.error(f"Erro ao processar vídeo do Instagram: {e}")
        await update.message.reply_text("Ocorreu um erro ao processar o vídeo.")

// ... existing code ...