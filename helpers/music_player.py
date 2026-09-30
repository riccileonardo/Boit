import asyncio
import discord
import yt_dlp

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

filas = {}

def buscar_audio(busca: str):
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
        info = ytdl.extract_info(f"ytsearch:{busca}" if not busca.startswith("http") else busca, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info.get('title', 'Música'), info['url']

async def tocar_proxima(guild, channel, client):
    if guild.id in filas and len(filas[guild.id]) > 0:
        musica = filas[guild.id].pop(0)
        source = discord.FFmpegPCMAudio(musica['url'], **FFMPEG_OPTIONS)
        voice_client = discord.utils.get(client.voice_clients, guild=guild)

        if voice_client and voice_client.is_connected():
            def after_playing(error):
                if error:
                    print(f"Erro na reprodução: {error}")
                asyncio.run_coroutine_threadsafe(tocar_proxima(guild, channel, client), client.loop)

            voice_client.play(source, after=after_playing)
            await channel.send(f"🎵 Tocando agora: **{musica['title']}**")
    else:
        await channel.send("✅ A fila de músicas terminou.")