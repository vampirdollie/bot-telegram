from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import datetime
import os
import random
import psycopg2

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

SUPERADMINS = ["7943521525"]

BLOQUEADOS = [
    "6378265355",
    "6905064136",
    "5353963160",
    "7740467368",
    "5515948854",
    "5760026959",
    "8124589828",
    "1296115044",
    "5924728043",
    "8504305248",
    "6727430013",
    "1470807173",
    "6911676625",
    "6813476131",
]

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS puntos(
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    score INTEGER DEFAULT 0
)
""")
conn.commit()

bolsas = {"A":0,"B":0,"C":0}
usos = {}
ultima_actualizacion = None
ultimo_obsequio = []

async def mensaje_bloqueo(update: Update):
    texto = """
⢀⣀ ⢀⣀
⢠⣯⢬⣷⡀ ⣴⡯⢌⣧
⠸⣿ ⠹⣷ ⢸⡝ ⢸⡿ ¡ pib pib pib !
⠻⣧⣀⣿⣦⣼⡁⣠⣿⠃
⢀⡾⠋ ⠈⣙⣯ el juego no está hecho
⣾ ⠸⡆ para admins. 👋🏻
⢰⡧⢄⢰⡆ ⢰⡆⡠⢄⣧
⠳⣼⣤⣤⣤⣤⣤⣧⠾⠁
"""
    await update.message.reply_text(texto)

# -------------------------------------------------------
# OBSEQUIO
# -------------------------------------------------------

async def obsequio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        await update.message.reply_text(
            "¡solo la admin puede repartir obsequios! 🐰"
        )
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            "usa:\n/obsequio <premio1> <premio2> <premio3>"
        )
        return

    try:
        premio1, premio2, premio3 = map(int, context.args)
    except ValueError:
        await update.message.reply_text(
            "los premios deben ser números."
        )
        return

    cur.execute("SELECT user_id, username FROM puntos")
    usuarios = cur.fetchall()

    if not usuarios:
        await update.message.reply_text(
            "todavía no hay jugadores registrados."
        )
        return

    global ultimo_obsequio
    ultimo_obsequio = []

    enviados = 0
    no_entregados = 0

    participantes = sum(
        1
        for target_id, _ in usuarios
        if str(target_id) not in BLOQUEADOS
    )

    premio_mayor = max(premio1, premio2, premio3)

    for target_id, username in usuarios:

        if str(target_id) in BLOQUEADOS:
            continue

        premio = random.choices(
            [premio1, premio2, premio3],
            weights=[50,35,15]
        )[0]

        cur.execute("""
            UPDATE puntos
            SET score = score + %s
            WHERE user_id = %s
        """,(premio,target_id))
        conn.commit()

        ultimo_obsequio.append((username,premio))

        conejito = " 🐰" if premio == premio_mayor else ""

        try:

            await context.bot.send_message(
                chat_id=int(target_id),
                text=(
                    "🐰 ¡El conejito pasó por aquí!\n\n"
                    f"Te dejó un obsequio de {premio} kooins{conejito}.\n\n"
                    "¡Espero que disfrutes tu regalito! ✿"
                )
            )

            enviados += 1

        except Exception:
            no_entregados += 1

    await update.message.reply_text(
        "🐰 El conejito salió a repartir regalos...\n\n"
        f"✿ Participantes: {participantes}\n"
        f"💬 Mensajes enviados: {enviados}\n"
        f"📭 No entregados: {no_entregados}\n\n"
        "¡Espero que todos disfruten su obsequio! 𖹭"
    )

# -------------------------------------------------------
# VER OBSEQUIO
# -------------------------------------------------------

async def verobsequio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    global ultimo_obsequio

    if not ultimo_obsequio:
        await update.message.reply_text(
            "todavía no has enviado ningún obsequio."
        )
        return

    premios = sorted(
        list(set(p for _, p in ultimo_obsequio)),
        reverse=True
    )

    mensaje = "🎁 Último obsequio\n\n"

    emojis = ["🐰","🌸","🍀"]

    for i, premio in enumerate(premios):

        emoji = emojis[i] if i < len(emojis) else "✨"

        mensaje += f"{emoji} Premio ({premio} kooins)\n"

        for username, valor in ultimo_obsequio:

            if valor == premio:
                mensaje += f"• {username}\n"

        mensaje += "\n"

    mensaje += f"Participantes: {len(ultimo_obsequio)}"

    await update.message.reply_text(mensaje)

# -------------------------------------------------------
# HANDLER PARA "."
# -------------------------------------------------------

async def texto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)

    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return

    texto = update.message.text.lower()

    if texto.startswith(".abrir"):
        await abrir(update, context)

    elif texto.startswith(".total"):
        await total(update, context)

    elif texto.startswith(".ranking"):
        await ranking(update, context)

    elif texto.startswith(".reset"):
        await reset(update, context)

    elif texto.startswith(".cmds"):
        await cmds(update, context)

    elif texto.startswith(".setbolsas"):
        await setbolsas(update, context)

    elif texto.startswith(".juegoinfo"):
        await juegoinfo(update, context)

    elif texto.startswith(".obsequio"):

        context.args = texto.split()[1:]
        await obsequio(update, context)

    elif texto.startswith(".verobsequio"):
        await verobsequio(update, context)


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cmds", cmds))
app.add_handler(CommandHandler("juegoinfo", juegoinfo))
app.add_handler(CommandHandler("abrir", abrir))
app.add_handler(CommandHandler("total", total))
app.add_handler(CommandHandler("ranking", ranking))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("setbolsas", setbolsas))
app.add_handler(CommandHandler("kooins", kooins))
app.add_handler(CommandHandler("obsequio", obsequio))
app.add_handler(CommandHandler("verobsequio", verobsequio))

app.add_handler(CallbackQueryHandler(elegir_bolsa))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        texto_handler
    )
)

app.run_webhook(
    listen="0.0.0.0",
    port=8000,
    url_path=TOKEN,
    webhook_url=f"https://bot-telegram-2-lcx9.onrender.com/{TOKEN}"
)
