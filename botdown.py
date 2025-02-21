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

// ... existing code ...