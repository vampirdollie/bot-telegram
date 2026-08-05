from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import datetime, json, os, random

import os

TOKEN = os.getenv("TELEGRAM_TOKEN")

ARCHIVO = "puntos.json"

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

# --- Cargar datos ---
if os.path.exists(ARCHIVO):
    with open(ARCHIVO, "r") as f:
        datos = json.load(f)
    puntos = datos.get("puntos", {})
    bolsas = datos.get("bolsas", {"A": 0, "B": 0, "C": 0})
    usos = {uid: datetime.date.fromisoformat(fecha) for uid, fecha in datos.get("usos", {}).items()}
    ultima_actualizacion = datetime.date.fromisoformat(datos.get("ultima_actualizacion")) if "ultima_actualizacion" in datos else None
else:
    puntos = {}
    bolsas = {"A": 0, "B": 0, "C": 0}
    usos = {}
    ultima_actualizacion = None

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
    await update.message.reply_photo(
        photo=open("start.jpg", "rb"),
        caption=mensaje_start
    )

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
    keyboard = [
        [InlineKeyboardButton("🐰", callback_data=str(valores[0]))],
        [InlineKeyboardButton("🐰", callback_data=str(valores[1]))],
        [InlineKeyboardButton("🐰", callback_data=str(valores[2]))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open("abrir.jpg", "rb"),
        caption=f":¨ ·.· ¨: ¡holi, {username}!\ndile fuera a la sal y elige tu fortuna de hoy.",
        reply_markup=reply_markup
    )

# --- ELEGIR BOLSA ---
async def elegir_bolsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    if user_id in BLOQUEADOS:
        # usamos tu mensaje personalizado
        await mensaje_bloqueo(update)
        return

    username = f"@{query.from_user.username}" if query.from_user.username else f"ID:{user_id}"
    premio = int(query.data)

    if user_id not in puntos:
        puntos[user_id] = {"score": 0, "username": username}
    puntos[user_id]["score"] += premio
    puntos[user_id]["username"] = username

    with open(ARCHIVO, "w") as f:
        json.dump({
            "puntos": puntos,
            "bolsas": bolsas,
            "usos": {uid: fecha.isoformat() for uid, fecha in usos.items()},
            "ultima_actualizacion": ultima_actualizacion.isoformat() if ultima_actualizacion else None
        }, f)

    # identificar el mayor valor del día
    max_valor = max(bolsas.values())
    extra = " 🐰" if premio == max_valor else ""

    await query.edit_message_caption(
        caption=f"{username}, elegiste y encontraste {premio} kooins{extra} ( ˶ •⩊• ˵ )"
    )

# --- TOTAL ---
async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return

    acumulado = puntos.get(user_id, {"score": 0})["score"]
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

    if not puntos or all(data["score"] == 0 for _, data in puntos.items()):
        await update.message.reply_text("(｡•́︿•̀｡) todavía nadie ha ganado puntos,\n¡sé el primero en ganar!")
        return

    ranking_lista = sorted(puntos.items(), key=lambda x: x[1]["score"], reverse=True)

    mensaje = "๑ ¡hola, admin!\nranking de participantes:\n\n"
    for i, (uid, data) in enumerate(ranking_lista, start=1):
        jugador = data["username"]
        if i == 1:
            icono = "🐰"
        elif i <= 3:
            icono = "⭐"
        else:
            icono = f"{i}."
        mensaje += f"{icono} {jugador}: {data['score']} kooins\n"

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

    for uid in puntos:
        puntos[uid]["score"] = 0

    usos.clear()

    with open(ARCHIVO, "w") as f:
        json.dump({
            "puntos": puntos,
            "bolsas": bolsas,
            "usos": {},
            "ultima_actualizacion": ultima_actualizacion.isoformat() if ultima_actualizacion else None
        }, f)

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

        with open(ARCHIVO, "w") as f:
            json.dump({
                "puntos": puntos,
                "bolsas": bolsas,
                "usos": {uid: fecha.isoformat() for uid, fecha in usos.items()},
                "ultima_actualizacion": ultima_actualizacion.isoformat()
            }, f)

        # identificar el mayor valor
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

        # si viene como @username, lo usamos directamente como nombre
        if objetivo.startswith("@"):
            target_id = objetivo  # lo guardamos como clave de texto
        else:
            target_id = objetivo  # puede ser un ID numérico

        # si no existe en puntos, lo creamos
        if target_id not in puntos:
            puntos[target_id] = {"score": 0, "username": objetivo}

        puntos[target_id]["score"] += cantidad
        puntos[target_id]["username"] = objetivo

        with open(ARCHIVO, "w") as f:
            json.dump({
                "puntos": puntos,
                "bolsas": bolsas,
                "usos": {uid: fecha.isoformat() for uid, fecha in usos.items()},
                "ultima_actualizacion": ultima_actualizacion.isoformat() if ultima_actualizacion else None
            }, f)

        await update.message.reply_text(
            f"¡se sumaron {cantidad} kooins a {puntos[target_id]['username']}!\n"
            f"ahora tiene {puntos[target_id]['score']} kooins. ٩(ˊᗜˋ*)و"
        )

    except ValueError:
        await update.message.reply_text("¡ups! la cantidad debe ser un número entero.")

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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_handler))

app.run_polling()
