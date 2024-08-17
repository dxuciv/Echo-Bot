import os
from datetime import datetime
import logging
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Configuración
load_dotenv()

TOKEN = os.environ.get("ECHO_TOKEN")
PREFIXO_COMANDO = os.environ.get("ECHO_PREFIXO_COMANDO")
EMOJI_SI = os.environ.get("ECHO_EMOJI_SI")
EMOJI_PUEDE = os.environ.get("ECHO_EMOJI_PUEDE")
EMOJI_NO = os.environ.get("ECHO_EMOJI_NO")

# Configuración de logging
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.WARNING)
log = logging.getLogger()
log.setLevel(logging.INFO)
logformat = logging.Formatter('[%(asctime)s] (%(levelname)s) %(message)s')
consolehandler = logging.StreamHandler()
consolehandler.setFormatter(logformat)
log.addHandler(consolehandler)

# Inicialización del bot
scheduler = AsyncIOScheduler()
scheduler.start()
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=PREFIXO_COMANDO, intents=intents)
bot.remove_command('help')

# Funciones auxiliares
async def enviar_recordatorio(ctx, tiempo, tema, mensaje_id):
    try:
        mensaje = await ctx.fetch_message(mensaje_id)
        lista_pings = await obtener_lista_pings(mensaje, ctx.message.guild)
        await ctx.reply(f"Es {tiempo.strftime('%H:%M')}, ¡hora de {tema}!\n{lista_pings}")
    except discord.NotFound:
        await ctx.send("No se pudo encontrar el mensaje.")

async def obtener_lista_pings(mensaje, guild):
    lista_pings = []
    for reaccion in mensaje.reactions:
        usuarios = await reaccion.users().flatten()
        if str(reaccion.emoji) == EMOJI_SI:
            for usuario in usuarios:
                if usuario.id != bot.user.id:
                    member = guild.get_member(usuario.id)
                    if member:
                        lista_pings.append(member.mention)
        if str(reaccion.emoji) == EMOJI_PUEDE:
            for usuario in usuarios:
                if usuario.id != bot.user.id:
                    member = guild.get_member(usuario.id)
                    if member:
                        lista_pings.append(member.mention)

    # Eliminar duplicados
    lista_pings = list(set(lista_pings))

    # Separar menciones
    lista_pings = ' '.join(lista_pings)

    return lista_pings

async def obtener_lista_rsvps(mensaje, guild):
    lista_rsvps = [[], [], []]
    for reaccion in mensaje.reactions:
        usuarios = await reaccion.users().flatten()
        if str(reaccion.emoji) == EMOJI_SI:
            for usuario in usuarios:
                if usuario.id != bot.user.id:
                    member = guild.get_member(usuario.id)
                    if member:
                        lista_rsvps[0].append(member.display_name)
        if str(reaccion.emoji) == EMOJI_PUEDE:
            for usuario in usuarios:
                if usuario.id != bot.user.id:
                    member = guild.get_member(usuario.id)
                    if member:
                        lista_rsvps[1].append(member.display_name)
        if str(reaccion.emoji) == EMOJI_NO:
            for usuario in usuarios:
                if usuario.id != bot.user.id:
                    member = guild.get_member(usuario.id)
                    if member:
                        lista_rsvps[2].append(member.display_name)

    lista_rsvps[0] = ', '.join(lista_rsvps[0])
    lista_rsvps[1] = ', '.join(lista_rsvps[1])
    lista_rsvps[2] = ', '.join(lista_rsvps[2])

    if not lista_rsvps[0]:
        lista_rsvps[0] = "-"
    if not lista_rsvps[1]:
        lista_rsvps[1] = "-"
    if not lista_rsvps[2]:
        lista_rsvps[2] = "-"

    return lista_rsvps

async def actualizar_mensaje_rsvp(mensaje, lista_rsvps):
    embed = discord.Embed(description="¿Quién viene? <a:eyesshaking:657904205490814996>")
    embed.add_field(name=f"{EMOJI_SI} sí", value=f"{lista_rsvps[0]}", inline=False)
    embed.add_field(name=f"{EMOJI_PUEDE} puede que sí", value=f"{lista_rsvps[1]}", inline=False)
    embed.add_field(name=f"{EMOJI_NO} no", value=f"{lista_rsvps[2]}", inline=False)

    await mensaje.edit(embed=embed)

# Eventos
@bot.event
async def on_ready():
    await bot.change_presence(
    activity=discord.Activity(type=discord.ActivityType.playing, name="CyberPunk 2077"))
    log.info('Iniciado sesión como: {0.user} (ID = {0.user.id})'.format(bot))
    log.info('¡Bot listo!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        log.warning(error)
        await ctx.send("Comando no encontrado <:peeposadcat:771066963211976774>")
        return
    raise error

@bot.check
async def bloquear_dms(ctx):
    if ctx.guild is not None:
        return True
    await ctx.send("No acepto mensajes directos <:9976_smiling_gun:657904189103407105>")
    return False

@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        return
    try:
        mensaje = await channel.fetch_message(payload.message_id)
        if payload.user_id == bot.user.id or mensaje.author.id != bot.user.id:
            return
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        lista_rsvps = await obtener_lista_rsvps(mensaje, guild)
        await actualizar_mensaje_rsvp(mensaje, lista_rsvps)
    except discord.NotFound:
        log.warning(f"Mensaje {payload.message_id} no encontrado.")
    except Exception as e:
        log.error(f"Error al procesar la reacción: {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        return
    try:
        mensaje = await channel.fetch_message(payload.message_id)
        if payload.user_id == bot.user.id or mensaje.author.id != bot.user.id:
            return
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        lista_rsvps = await obtener_lista_rsvps(mensaje, guild)
        await actualizar_mensaje_rsvp(mensaje, lista_rsvps)
    except discord.NotFound:
        log.warning(f"Mensaje {payload.message_id} no encontrado.")
    except Exception as e:
        log.error(f"Error al procesar la reacción: {e}")

# Comandos
@bot.command(name='Ayuda')
async def help(ctx):
    await ctx.send(
        f"🕒 **Hola, soy EchoBot!**\n"
        f"Puedo ayudarte a gestionar eventos, recoger RSVPs y recordar a todos los que respondieron 'sí' o 'quizás' cuando comience el evento.\n\n"
        f"💬 **Comandos**\n"
        f"``{PREFIXO_COMANDO}add HH:MM título del evento`` añade un evento\n"
        f"``{PREFIXO_COMANDO}events`` lista los eventos próximos")

@bot.command(name='add')
async def add(ctx, tiempo, *, tema):
    try:
        tiempo = datetime.strptime(tiempo, "%H:%M")
    except ValueError:
        await ctx.send("Por favor, formatea tu hora de esta manera: 19:30")
        return

    hoy = datetime.today()
    tiempo = tiempo.replace(year=hoy.year, month=hoy.month, day=hoy.day)

    embed = discord.Embed(description="¿Quién viene? <a:eyesshaking:657904205490814996>")
    embed.add_field(name=f"{EMOJI_SI} sí", value="-", inline=False)
    embed.add_field(name=f"{EMOJI_PUEDE} puede que sí", value="-", inline=False)
    embed.add_field(name=f"{EMOJI_NO} no", value="-", inline=False)

    mensaje = await ctx.send(f"**[{tiempo.strftime('%H:%M')}] {tema}**", embed=embed)

    reacciones = [EMOJI_SI, EMOJI_PUEDE, EMOJI_NO]
    for reaccion in reacciones:
        await mensaje.add_reaction(reaccion)

    scheduler.add_job(enviar_recordatorio, args=[ctx, tiempo, tema, mensaje.id], trigger='date', run_date=tiempo)

@bot.command(name='events')
async def events(ctx):
    lista_trabajos = scheduler.get_jobs()
    lista_eventos = ""
    for trabajo in lista_trabajos:
        nombre_evento = trabajo.args[2]
        tiempo_evento = datetime.strftime(trabajo.next_run_time, "%H:%M")
        lista_eventos += f"**[{tiempo_evento}]** {nombre_evento}\n"
    if lista_eventos:
        await ctx.send(f"{lista_eventos}")
    else:
        await ctx.send("No hay eventos próximos <:pepehmm:769982318369701898>")

log.info("### Iniciando bot ###")
bot.run(TOKEN)
