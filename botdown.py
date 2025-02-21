import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import requests
import instaloader
from pytube import YouTube
from queue import Queue
from datetime import datetime, timedelta
import traceback
import json
import hashlib
import time
from collections import defaultdict
from typing import Optional, Dict, List

# Configuração do logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações globais
CACHE_DIR = "cache"
STATS_FILE = "stats.json"
ERROR_LOG_FILE = "error_log.txt"
MAX_QUEUE_SIZE = 10
RATE_LIMIT = 5
RATE_LIMIT_PERIOD = 60

# Criação de diretórios necessários
os.makedirs(CACHE_DIR, exist_ok=True)

# Configurações de qualidade de vídeo
VIDEO_QUALITIES = {
    'low': '360p',
    'medium': '720p',
    'high': '1080p'
}

# Inicialização das estruturas de dados
download_queue: Queue = Queue()
rate_limit_dict: Dict[int, List[float]] = defaultdict(list)

class StatsManager:
    def __init__(self, stats_file: str):
        self.stats_file = stats_file
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict:
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {"downloads": 0, "users": {}, "platforms": {}}
    
    def update_stats(self, user_id: int, platform: str) -> None:
        self.stats["downloads"] += 1
        self.stats["users"][str(user_id)] = self.stats["users"].get(str(user_id), 0) + 1
        self.stats["platforms"][platform] = self.stats["platforms"].get(platform, 0) + 1
        self._save_stats()
    
    def _save_stats(self) -> None:
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f)
    
    def get_stats(self) -> Dict:
        return self.stats

stats_manager = StatsManager(STATS_FILE)

def log_error(error: Exception, user_id: int, command: str) -> None:
    with open(ERROR_LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_details = f"""
        Timestamp: {timestamp}
        User ID: {user_id}
        Command: {command}
        Error: {str(error)}
        Traceback: {traceback.format_exc()}
        ------------------------
        """
        f.write(error_details)

def get_cached_video(url: str) -> Optional[str]:
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{url_hash}.mp4")
    
    if os.path.exists(cache_path) and time.time() - os.path.getmtime(cache_path) < 24*60*60:
        return cache_path
    return None

def save_to_cache(url: str, file_path: str) -> str:
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{url_hash}.mp4")
    os.rename(file_path, cache_path)
    return cache_path

def check_file_size(file_path: str, max_size_mb: int = 50) -> bool:
    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Converter para MB
        return file_size <= max_size_mb
    except OSError:
        return False

def is_valid_url(url: str) -> bool:
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_quality_keyboard(video_url: str, platform: str) -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton("360p", callback_data=f"{platform}|{video_url}|low"),
        InlineKeyboardButton("720p", callback_data=f"{platform}|{video_url}|medium"),
        InlineKeyboardButton("1080p", callback_data=f"{platform}|{video_url}|high")
    ]]
    return InlineKeyboardMarkup(keyboard)

async def download_video(platform: str, url: str, quality: str) -> Optional[str]:
    try:
        if platform == "youtube":
            return await download_youtube_video(url, VIDEO_QUALITIES[quality])
        elif platform == "instagram":
            return await download_instagram_video(url, VIDEO_QUALITIES[quality])
        elif platform == "tiktok":
            return await download_tiktok_video(url, VIDEO_QUALITIES[quality])
        return None
    except Exception as e:
        logger.error(f"Erro ao baixar vídeo: {e}")
        return None

async def download_youtube_video(url: str, quality: str) -> Optional[str]:
    try:
        # Adicionar headers para simular um navegador
        yt = YouTube(url, use_oauth=True, allow_oauth_cache=True)
        
        # Tentar obter o stream com a qualidade solicitada
        stream = yt.streams.filter(progressive=True, file_extension="mp4", resolution=quality).first()
        
        # Se não encontrar a qualidade desejada, tentar encontrar a melhor qualidade disponível
        if not stream:
            logger.info(f"Qualidade {quality} não disponível. Buscando melhor qualidade disponível.")
            stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
        
        if stream:
            file_path = f"/tmp/youtube_video_{int(time.time())}.mp4"  # Nome único para evitar conflitos
            stream.download(output_path="/tmp", filename=os.path.basename(file_path))
            logger.info(f"Vídeo baixado com sucesso: {file_path}")
            return file_path
            
        logger.error("Nenhum stream disponível para download")
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
        # Implementação real necessária - atual é apenas placeholder
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

# Handlers dos comandos
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
    🤖 *Bot de Download de Vídeos*
    
    Comandos disponíveis:
    /instagram <link> - Baixar vídeo do Instagram
    /tiktok <link> - Baixar vídeo do TikTok
    /youtube <link> - Baixar vídeo do YouTube Shorts
    /stats - Visualizar estatísticas do bot
    /queue - Ver status da fila de downloads
    /help - Mostrar esta mensagem de ajuda
    
    ⚠️ Limite máximo de arquivo: 200MB
    ⏱️ Limite de uso: 5 downloads por minuto
    
    📦 Os vídeos são armazenados em cache por 24 horas
    🎥 Suporte a diferentes qualidades de vídeo
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Função para lidar com comando /instagram
async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        url = context.args[0]
        if not is_valid_url(url):
            await update.message.reply_text("❌ URL inválida. Por favor, verifique o link e tente novamente.")
            return
            
        await update.message.reply_text("⏳ Baixando vídeo... Por favor, aguarde.")
        file_path = download_instagram_video(url)
        
        if file_path and check_file_size(file_path):
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Erro: Arquivo muito grande ou download falhou. Tente outro vídeo.")
    else:
        await update.message.reply_text("⚠️ Por favor, forneça um link do Instagram após o comando. Exemplo: /instagram <link_do_video>")

# Função para lidar com comando /tiktok
async def handle_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        url = context.args[0]
        file_path = download_tiktok_video(url)
        if file_path:
            await update.message.reply_video(video=open(file_path, 'rb'))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Não consegui baixar o vídeo do TikTok. Tente novamente.")
    else:
        await update.message.reply_text("⚠️ Por favor, forneça um link do TikTok após o comando. Exemplo: /tiktok <link_do_video>")

# Função para lidar com comando /youtube
async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor, forneça um link do YouTube após o comando. Exemplo: /youtube <link_do_video>"
        )
        return

    url = context.args[0]
    if not is_valid_url(url):
        await update.message.reply_text("❌ URL inválida. Por favor, verifique o link e tente novamente.")
        return

    cached_path = get_cached_video(url)
    if cached_path:
        await update.message.reply_text("📦 Enviando vídeo do cache...")
        await update.message.reply_video(video=open(cached_path, 'rb'))
        stats_manager.update_stats(update.effective_user.id, "youtube")
        return

    await update.message.reply_text(
        "🎥 Selecione a qualidade do vídeo:",
        reply_markup=get_quality_keyboard(url, "youtube")
    )

# Função para ver status da fila
async def handle_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    queue_size = download_queue.qsize()
    await update.message.reply_text(
        f"📊 Status da fila de downloads:\n"
        f"- Downloads em andamento: {queue_size}\n"
        f"- Capacidade máxima: {MAX_QUEUE_SIZE}\n"
        f"- Disponível: {MAX_QUEUE_SIZE - queue_size}"
    )

# Função para lidar com comando /stats
async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats = stats_manager.get_stats()
    stats_text = f"""
    📊 *Estatísticas do Bot*
    
    Total de downloads: {stats['downloads']}
    
    Downloads por plataforma:
    - YouTube: {stats['platforms'].get('youtube', 0)}
    - Instagram: {stats['platforms'].get('instagram', 0)}
    - TikTok: {stats['platforms'].get('tiktok', 0)}
    
    Usuários ativos: {len(stats['users'])}
    """
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    platform, url, quality = query.data.split("|")
    
    await query.answer()
    await query.edit_message_text("⏳ Baixando vídeo... Por favor, aguarde.")
    
    if download_queue.qsize() >= MAX_QUEUE_SIZE:
        await query.edit_message_text("❌ Fila de downloads cheia. Tente novamente mais tarde.")
        return
        
    # Verificar limite de taxa
    user_id = update.effective_user.id
    current_time = time.time()
    rate_limit_dict[user_id] = [t for t in rate_limit_dict[user_id] if current_time - t < RATE_LIMIT_PERIOD]
    
    if len(rate_limit_dict[user_id]) >= RATE_LIMIT:
        await query.edit_message_text("⚠️ Limite de downloads atingido. Aguarde um minuto.")
        return
    
    rate_limit_dict[user_id].append(current_time)
    
    try:
        file_path = await download_video(platform, url, quality)
        
        if file_path and check_file_size(file_path):
            cached_path = save_to_cache(url, file_path)
            await query.message.reply_video(video=open(cached_path, 'rb'))
            stats_manager.update_stats(user_id, platform)
        else:
            await query.edit_message_text("❌ Erro: Arquivo muito grande ou download falhou. Tente outro vídeo.")
    except Exception as e:
        log_error(e, user_id, f"download_{platform}")
        await query.edit_message_text("❌ Ocorreu um erro durante o download. Tente novamente.")

# Função principal para iniciar o bot
def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ Token do bot não encontrado. Configure a variável de ambiente 'TELEGRAM_BOT_TOKEN'.")
        return

    application = Application.builder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("instagram", handle_instagram))
    application.add_handler(CommandHandler("tiktok", handle_tiktok))
    application.add_handler(CommandHandler("youtube", handle_youtube))
    application.add_handler(CommandHandler("stats", handle_stats))
    application.add_handler(CommandHandler("queue", handle_queue))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Handler para comandos desconhecidos
    application.add_handler(MessageHandler(
        filters.COMMAND,
        lambda u, c: u.message.reply_text("❌ Comando desconhecido. Use /help para ver os comandos disponíveis.")
    ))

    logger.info("✅ Bot iniciado com sucesso!")
    application.run_polling()

if __name__ == "__main__":
    main()
