from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import datetime, os, random
import psycopg2

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

SUPERADMINS = ["7943521525"]  # solo tú

# --- Bloqueados ---
BLOQUEADOS = [
    "6378265355", # liss
    "6905064136", # valu
    "5353963160", # ali
    "7740467368", # pau
    "5515948854", # paris
    "5760026959", # lia
    "8124589828", # leis
    "1296115044", # bel
    "5924728043", # gum
    "8504305248", # meli
    "6727430013", # neo
    "1470807173", # mika
    "6911676625", # castillo
    "6813476131"  # cat
]

def esta_bloqueado(user_id):
    return str(user_id) in BLOQUEADOS

# --- Conexión a Postgres ---
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS puntos (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    score INTEGER DEFAULT 0
)
""")
conn.commit()

# --- Variables en memoria para bolsas y usos ---
bolsas = {"A": 0, "B": 0, "C": 0}
usos = {}
ultima_actualizacion = None

async def mensaje_bloqueo(update: Update):
    texto = """⠀⢀⣀⠀⠀⠀⠀⠀⢀⣀⠀
⢠⣯⢬⣷⡀⠀⠀⣴⡯⢌⣧
⠸⣿⠀⠹⣷⠀⢸⡝⠀⢸⡿⠀⠀⠀   ¡ pib pib pib !
⠀⠻⣧⣀⣿⣦⣼⡁⣠⣿⠃
⠀⢀⡾⠋⠀⠀⠀⠈⣙⣯⠀  el juego no está hecho
⠀⣾⠀⠀⠀⠀⠀⠀⠀⠸⡆        para admins. 👋🏻
⢰⡧⢄⢰⡆⠀⢰⡆⡠⢄⣧
⠀⠳⣼⣤⣤⣤⣤⣤⣧⠾⠁
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""
    await update.message.reply_text(texto)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    mensaje_start = """⠀⠀⠀ ⠀⠀⠀¡holi, personita! (ृ '꒳' ृ)
⠀⠀⠀  ⠀ ⠀bienvenida/o al bot que
⠀⠀⠀⠀  ⠀ ⠀⠀probará tu suerte.

⠀⠀⠀๑ para conocer los comandos
⠀⠀⠀⠀⠀⠀⠀usa ".cmds" o "/cmds"

⠀eso sería todo por ahora, ¡hasta luego! 𖹭"""
    await update.message.reply_photo(photo=open("start.jpg", "rb"), caption=mensaje_start)

# --- CMDS ---
async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    mensaje = """⠀
/juegoinfo → ¿cómo funciona la dinámica?
/abrir → empezar a jugar
❕ : solo un intento por día
/total → ver tu acumulado
/start → bienvenida
/cmds → lista de comandos

❕ : comandos para admins
/ranking → ¿cuánto lleva cada participante?
/reset → reiniciar puntos
/setbolsas → cambiar valores
/kooins → dar kooins a un participante

๑ cada comando funciona también con punto "." al inicio.
⠀"""
    await update.message.reply_text(mensaje)

# --- JUEGOINFO ---
async def juegoinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    mensaje = """⠀⠀⠀
 ׄ𑊑ᰍㅤׄinfo :

๑ solo tienes un intento por día.
๑ los valores se cambian diariamente.
🐰 ! podrás encontrar cajitas con un conejo dorado (identificado con el emoji de conejo al recibir tus kooins); lo que significa más puntos.
๑ si intentas jugar antes de que se actualicen las cajitas, el bot te avisará y no gastarás tu intento.
๑ la fortuna acumulada se mide en 𝗸𝗼𝗼𝗶𝗻𝘀.

¡diviértete y prueba tu suerte cada día! ⊹ ˖ Ი𐑼
⠀⠀⠀"""
    await update.message.reply_text(mensaje)

# --- ABRIR ---
async def abrir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    hoy = datetime.date.today()
    if ultima_actualizacion != hoy:
        await update.message.reply_text("✿ Las cajitas aún no están listas, espera a que la admin las configure.")
        return
    if user_id in usos and usos[user_id] == hoy:
        await update.message.reply_text("ya gastaste tu intento, vuelve luego con más suerte. 𖹭")
        return
    usos[user_id] = hoy
    username = f"@{update.effective_user.username}" if update.effective_user.username else f"ID:{user_id}"
    valores = list(bolsas.values())
    random.shuffle(valores)
    keyboard = [[InlineKeyboardButton("🐰", callback_data=str(valores[i]))] for i in range(3)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(photo=open("abrir.jpg", "rb"),
        caption=f":¨ ·.· ¨: ¡holi, {username}!\ndile fuera a la sal y elige tu fortuna de hoy.",
        reply_markup=reply_markup)

# --- ELEGIR BOLSA ---
async def elegir_bolsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    username = f"@{query.from_user.username}" if query.from_user.username else f"ID:{user_id}"
    premio = int(query.data)
    cur.execute("""
    INSERT INTO puntos (user_id, username, score)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id) DO UPDATE
    SET score = puntos.score + EXCLUDED.score,
        username = EXCLUDED.username
    """, (user_id, username, premio))
    conn.commit()
    max_valor = max(bolsas.values())
    extra = " 🐰" if premio == max_valor else ""
    await query.edit_message_caption(caption=f"{username}, elegiste y encontraste {premio} kooins{extra} ( ˶ •⩊• ˵ )")

# --- TOTAL ---
async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    cur.execute("SELECT score FROM puntos WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    acumulado = row[0] if row else 0
    await update.message.reply_text(f"tu fortuna actual es: {acumulado} kooins. ✿")

# --- RANKING ---
async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    if user_id not in SUPERADMINS:
        await update.message.reply_text("el ranking es privado, solo admins pueden verlo. ¡qué nervios!")
        return
    # Consultar todos los usuarios ordenados por score
    cur.execute("SELECT username, score FROM puntos ORDER BY score DESC")
    rows = cur.fetchall()
    if not rows:
        await update.message.reply_text("(｡•́︿•̀｡) todavía nadie ha ganado puntos,\n¡sé el primero en ganar!")
        return
    mensaje = "๑ ¡hola, admin!\nranking de participantes:\n\n"
    for i, (jugador, score) in enumerate(rows, start=1):
        if i == 1:
            icono = "🐰"
        elif i <= 3:
            icono = "⭐"
        else:
            icono = f"{i}."
        mensaje += f"{icono} {jugador}: {score} kooins\n"
    await update.message.reply_text(mensaje)

# --- RESET ---
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    if user_id not in SUPERADMINS:
        await update.message.reply_text("¡solo la admin puede reiniciar los puntos!")
        return
    cur.execute("UPDATE puntos SET score = 0")
    conn.commit()
    usos.clear()
    await update.message.reply_text("se ha reiniciado el ranking, todos vuelven a cero. (╥ ╥)")

# --- SET BOLSAS ---
async def setbolsas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return
    if user_id not in SUPERADMINS:
        await update.message.reply_text("solo la admin puede cambiar los valores de las bolsas.")
        return
    try:
        a, b, c = map(int, context.args)
        global bolsas, ultima_actualizacion
        bolsas = {"A": a, "B": b, "C": c}
        ultima_actualizacion = datetime.date.today()
        max_valor = max(a, b, c)
        mensaje = "¡valores actualizados!\n"
        mensaje += f"A = {a} kooins {'🐰' if a == max_valor else ''}\n"
        mensaje += f"B = {b} kooins {'🐰' if b == max_valor else ''}\n"
        mensaje += f"C = {c} kooins {'🐰' if c == max_valor else ''}"
        await update.message.reply_text(mensaje)
    except:
        await update.message.reply_text("⚠️ : usa el formato: /setbolsas <A> <B> <C>")

# --- KOOINS (solo admin) ---
async def kooins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in SUPERADMINS:
        await update.message.reply_text("¡alto ahí, velocista! este comando solo lo puede usar la admin.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("usa el formato /kooins <cantidad> @usuario")
        return
    try:
        cantidad = int(context.args[0])
        objetivo = context.args[1]
        if objetivo.startswith("@"):
            # Buscar el user_id real en la tabla usando el username
            cur.execute("SELECT user_id FROM puntos WHERE username=%s", (objetivo,))
            row = cur.fetchone()
            if not row:
                await update.message.reply_text("ese usuario aún no ha jugado, no puedo darle kooins. ૮◞ ◟ ა")
                return
            target_id = row[0]   # usamos el user_id real
            username = objetivo
        else:
            # si se pasa un ID numérico directamente
            target_id = objetivo
            username = f"ID:{objetivo}"

        if esta_bloqueado(target_id):
            await update.message.reply_text(
                "no puedes entregar kooins a este usuario."
            )
            return

        cur.execute(
            "UPDATE puntos SET score = score + %s, username = %s WHERE user_id = %s",
            (cantidad, username, target_id)
        )
        conn.commit()
        # Consultar acumulado correcto
        cur.execute("SELECT score FROM puntos WHERE user_id=%s", (target_id,))
        row = cur.fetchone()
        acumulado = row[0] if row else cantidad
        await update.message.reply_text(
            f"¡se sumaron {cantidad} kooins a {username}!\n"
            f"ahora tiene {acumulado} kooins. ٩(ˊᗜˋ*)و"
        )
    except ValueError:
        await update.message.reply_text("¡ups! la cantidad debe ser un número entero.")

# --- OBSEQUIO (solo admin) ---
ultimo_obsequio = []

async def obsequio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        await update.message.reply_text(
            "¡solo la admin puede repartir obsequios! 🐰"
        )
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            "usa el formato:\n/obsequio <premio1> <premio2> <premio3>"
        )
        return

    try:
        premio1, premio2, premio3 = map(int, context.args)
    except ValueError:
        await update.message.reply_text(
            "los premios deben ser números enteros."
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
            weights=[50, 35, 15]
        )[0]

        cur.execute(
            """
            UPDATE puntos
            SET score = score + %s
            WHERE user_id = %s
            """,
            (premio, target_id)
        )

        conn.commit()

        ultimo_obsequio.append((username, premio))

        conejito = " 🐰" if premio == premio_mayor else ""

        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=(
                    "🐰 ¡El conejito pasó por aquí!\n\n"
                    f"Te dejó un obsequio de "
                    f"{premio} kooins{conejito}.\n\n"
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


# --- VER OBSEQUIO (solo admin) ---

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

    mensaje = "๑ último obsequio\n\n"

    emojis = ["🐰", "🌸", "🍀"]

    for i, premio in enumerate(premios):

        emoji = emojis[i] if i < len(emojis) else "✨"

        mensaje += f"{emoji} premio ({premio} kooins)\n"

        for username, valor in ultimo_obsequio:
            if valor == premio:
                mensaje += f"• {username}\n"

        mensaje += "\n"

    mensaje += f"๑ participantes: {len(ultimo_obsequio)}"

    await update.message.reply_text(mensaje)

# --- HANDLER PARA "." ---
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

# --- MAIN ---
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cmds", cmds))
app.add_handler(CommandHandler("juegoinfo", juegoinfo))
app.add_handler(CommandHandler("abrir", abrir))
app.add_handler(CommandHandler("total", total))
app.add_handler(CommandHandler("ranking", ranking))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CommandHandler("setbolsas", setbolsas))
app.add_handler(CallbackQueryHandler(elegir_bolsa))
app.add_handler(CommandHandler("kooins", kooins))
app.add_handler(CommandHandler("obsequio", obsequio))
app.add_handler(CommandHandler("verobsequio", verobsequio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_handler))

# Aquí cambias polling por webhook
app.run_webhook(
    listen="0.0.0.0",
    port=8000,
    url_path=TOKEN,
    webhook_url=f"https://bot-telegram-2-lcx9.onrender.com/{TOKEN}"
)
