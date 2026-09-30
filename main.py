import os
from dotenv import load_dotenv

# O load_dotenv() DEVE vir antes da importação dos helpers
load_dotenv()

import discord
from datetime import datetime, timezone

from helpers.ranking_manager import carregar_ranking, registrar_tempo_voz
from helpers.ai_service import obter_resposta_ia
from helpers.music_player import filas, buscar_audio, tocar_proxima

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)
entradas_voz = {}

@client.event
async def on_ready():
    print(f'🤖 Bot conectado com sucesso como {client.user}')

@client.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    user_id = str(member.id)

    if before.channel is None and after.channel is not None:
        entradas_voz[user_id] = datetime.now(timezone.utc)
        print(f"🎙️ {member.name} entrou no canal de voz: {after.channel.name}")

    elif before.channel is not None and after.channel is None:
        if user_id in entradas_voz:
            minutos = registrar_tempo_voz(user_id, entradas_voz.pop(user_id))
            print(f"🚪 {member.name} saiu do canal de voz. Tempo registrado: {minutos} min")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 1. IA
    if message.content.startswith('!ia'):
        prompt = message.content[3:].strip()
        if not prompt:
            await message.channel.send("Por favor, digite uma pergunta após o comando `!ia`.")
            return

        async with message.channel.typing():
            try:
                resposta = await obter_resposta_ia(prompt)
                for i in range(0, len(resposta), 2000):
                    await message.channel.send(resposta[i:i+2000])
            except Exception as e:
                await message.channel.send(f"Erro na IA: {e}")

    # 2. RANKING
    elif message.content.startswith('!ranking'):
        ranking = carregar_ranking()
        if not ranking:
            await message.channel.send("📊 Ainda não há nenhum registro de tempo em chamadas de voz!")
            return

        top_usuarios = sorted(ranking.items(), key=lambda item: item[1], reverse=True)[:10]
        texto = "🏆 **Ranking de Tempo em Calls (Top 10)** 🏆\n\n"
        
        for posicao, (user_id, total_segundos) in enumerate(top_usuarios, start=1):
            horas, minutos = total_segundos // 3600, (total_segundos % 3600) // 60
            try:
                user = await client.fetch_user(int(user_id))
                nome = user.name if user else f"Usuário ({user_id})"
            except Exception:
                nome = f"Usuário ({user_id})"
            texto += f"**{posicao}º** - {nome} ➔ `{horas}h {minutos}m`\n"

        await message.channel.send(texto)

    # 3. TOCAR MÚSICA
    elif message.content.startswith('!tocar'):
        if not message.author.voice:
            await message.channel.send("❌ Você precisa estar em um canal de voz para tocar música!")
            return

        busca = message.content[7:].strip()
        if not busca:
            await message.channel.send("❌ Digite o nome da música ou o link do YouTube.")
            return

        voice_channel = message.author.voice.channel
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)

        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        async with message.channel.typing():
            try:
                titulo, url_audio = buscar_audio(busca)
                if message.guild.id not in filas:
                    filas[message.guild.id] = []

                if voice_client.is_playing() or voice_client.is_paused():
                    filas[message.guild.id].append({'title': titulo, 'url': url_audio})
                    await message.channel.send(f"📌 **{titulo}** adicionada à fila (Posição #{len(filas[message.guild.id])})!")
                else:
                    filas[message.guild.id].append({'title': titulo, 'url': url_audio})
                    await tocar_proxima(message.guild, message.channel, client)
            except Exception as e:
                await message.channel.send(f"❌ Ocorreu um erro ao buscar a música: {e}")

    # 4. PULAR MÚSICA
    elif message.content.startswith('!pular') or message.content.startswith('!skip'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await message.channel.send("⏭️ Música pulada!")
        else:
            await message.channel.send("❌ Nenhuma música está tocando no momento.")

    # 5. VER FILA
    elif message.content.startswith('!fila') or message.content.startswith('!queue'):
        guild_id = message.guild.id
        if guild_id in filas and len(filas[guild_id]) > 0:
            texto = "🎶 **Fila de Músicas:**\n\n" + "\n".join([f"**{i}.** {m['title']}" for i, m in enumerate(filas[guild_id], 1)])
            await message.channel.send(texto)
        else:
            await message.channel.send("📜 A fila de músicas está vazia.")

    # 6. PAUSAR / CONTINUAR
    elif message.content.startswith('!pausar'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await message.channel.send("⏸️ Música pausada!")

    elif message.content.startswith('!continuar') or message.content.startswith('!resume'):
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await message.channel.send("▶️ Música retomada!")

    # 7. PARAR
    elif message.content.startswith('!parar'):
        if message.guild.id in filas:
            filas[message.guild.id].clear()
        voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_connected():
            voice_client.stop()
            await voice_client.disconnect()
            await message.channel.send("⏹️ Música parada, fila limpa e bot desconectado!")

    # 8. COMANDO PERSONALIZADO
    elif message.content.startswith('!mugir'):
        await message.channel.send(f"🐂 Boi **{message.author.display_name}** está mugindo e chamando os bois! 🐄")

    # 9. AJUDA
    elif message.content.startswith('!ajuda') or message.content.startswith('!help'):
        embed = discord.Embed(title="🤖 Comandos do Boit", color=discord.Color.blue())
        embed.add_field(name="🎵 Música", value="`!tocar`, `!fila`, `!pular`, `!pausar`, `!continuar`, `!parar`", inline=False)
        embed.add_field(name="🤖 Utilitários", value="`!ia <pergunta>`, `!ranking`, `!mugir`", inline=False)
        await message.channel.send(embed=embed)

client.run(DISCORD_TOKEN)