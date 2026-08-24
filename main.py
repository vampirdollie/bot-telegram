from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import datetime, os, random
from zoneinfo import ZoneInfo
import psycopg2

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
KOALA_CHAT_ID = os.getenv("KOALA_CHAT_ID")
ZONA_COLOMBIA = ZoneInfo("America/Bogota")

SUPERADMINS = ["7943521525"]  # solo tú

# --- Bloqueados ---
BLOQUEADOS = [
    "6378265355", # liss
    "5353963160", # ali
    "5760026959", # lia
    "965030471", # pau
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
ultima_actualizacion = None
# --- Cargar configuración guardada ---
cur.execute("""
SELECT bolsa_a, bolsa_b, bolsa_c, fecha
FROM configuracion
WHERE id = 1
""")

row = cur.fetchone()

if row:
    bolsas = {
        "A": row[0],
        "B": row[1],
        "C": row[2]
    }
    ultima_actualizacion = row[3]

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

    hoy = datetime.datetime.now(ZONA_COLOMBIA).date()

    if ultima_actualizacion != hoy:
        await update.message.reply_text(
            "✿ Las cajitas aún no están listas, espera a que la admin las configure."
        )
        return

    # --- Comprobar si ya jugó hoy ---
    cur.execute(
        "SELECT fecha FROM usos WHERE user_id = %s",
        (user_id,)
    )

    row = cur.fetchone()

    if row and row[0] == hoy:
        await update.message.reply_text(
            "ya gastaste tu intento, vuelve luego con más suerte. 𖹭"
        )
        return

    # --- Registrar el intento en PostgreSQL ---
    cur.execute(
        """
        INSERT INTO usos (user_id, fecha)
        VALUES (%s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET fecha = EXCLUDED.fecha
        """,
        (user_id, hoy)
    )

    conn.commit()

    username = (
        f"@{update.effective_user.username}"
        if update.effective_user.username
        else f"ID:{user_id}"
    )

    valores = list(bolsas.values())
    random.shuffle(valores)

    keyboard = [
        [InlineKeyboardButton("🐰", callback_data=str(valores[i]))]
        for i in range(3)
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open("abrir.jpg", "rb"),
        caption=(
            f":¨ ·.· ¨: ¡holi, {username}!\n"
            "dile fuera a la sal y elige tu fortuna de hoy."
        ),
        reply_markup=reply_markup
    )

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
        await update.message.reply_text(
            "¡solo la admin puede reiniciar los puntos!"
        )
        return

    # Reiniciar puntos
    cur.execute("UPDATE puntos SET score = 0")

    # Reiniciar los intentos diarios
    cur.execute("DELETE FROM usos")

    conn.commit()

    await update.message.reply_text(
        "se ha reiniciado el ranking y los intentos. "
        "todos vuelven a cero y pueden jugar nuevamente. (╥ ╥)"
    )
# --- SET BOLSAS ---
async def setbolsas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return

    if user_id not in SUPERADMINS:
        await update.message.reply_text(
            "solo la admin puede cambiar los valores de las bolsas."
        )
        return

    try:
        a, b, c = map(int, context.args)

        global bolsas, ultima_actualizacion

        bolsas = {"A": a, "B": b, "C": c}
        ultima_actualizacion = datetime.datetime.now(ZONA_COLOMBIA).date()

        # Guardar configuración en PostgreSQL
        cur.execute("""
            INSERT INTO configuracion
            (id, bolsa_a, bolsa_b, bolsa_c, fecha)
            VALUES (1, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                bolsa_a = EXCLUDED.bolsa_a,
                bolsa_b = EXCLUDED.bolsa_b,
                bolsa_c = EXCLUDED.bolsa_c,
                fecha = EXCLUDED.fecha
        """, (
            a,
            b,
            c,
            ultima_actualizacion
        ))

        conn.commit()

        max_valor = max(a, b, c)

        mensaje = "¡valores actualizados!\n"
        mensaje += f"A = {a} kooins {'🐰' if a == max_valor else ''}\n"
        mensaje += f"B = {b} kooins {'🐰' if b == max_valor else ''}\n"
        mensaje += f"C = {c} kooins {'🐰' if c == max_valor else ''}"

        await update.message.reply_text(mensaje)

    except:
        await update.message.reply_text(
            "⚠️ : usa el formato: /setbolsas <A> <B> <C>"
        )

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

    # Crear un número para identificar este reparto
    cur.execute("SELECT COALESCE(MAX(lote), 0) + 1 FROM obsequios")
    lote = cur.fetchone()[0]

    enviados = 0
    no_entregados = 0

    participantes = sum(
        1
        for target_id, _ in usuarios
        if str(target_id) not in BLOQUEADOS
    )

    premio_mayor = max(premio1, premio2, premio3)

    for target_id, username in usuarios:

        # Los bloqueados NO reciben obsequio
        if str(target_id) in BLOQUEADOS:
            continue

        premio = random.choices(
            [premio1, premio2, premio3],
            weights=[50, 35, 15]
        )[0]

        # Guardar el premio en PostgreSQL
        cur.execute(
            """
            INSERT INTO obsequios
            (lote, user_id, username, premio)
            VALUES (%s, %s, %s, %s)
            """,
            (lote, target_id, username, premio)
        )

        # Sumar el premio a sus kooins
        cur.execute(
            """
            UPDATE puntos
            SET score = score + %s
            WHERE user_id = %s
            """,
            (premio, target_id)
        )

        conn.commit()

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
        "¡Esperamos que todos disfruten su obsequio! 𖹭"
    )


# --- VER OBSEQUIO (solo admin) ---

async def verobsequio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar el último reparto realizado
    cur.execute("""
        SELECT lote
        FROM obsequios
        ORDER BY lote DESC
        LIMIT 1
    """)

    row = cur.fetchone()

    if not row:
        await update.message.reply_text(
            "todavía no has enviado ningún obsequio."
        )
        return

    ultimo_lote = row[0]

    # Obtener los premios del último reparto
    cur.execute("""
        SELECT username, premio
        FROM obsequios
        WHERE lote = %s
        ORDER BY premio DESC
    """, (ultimo_lote,))

    filas = cur.fetchall()

    if not filas:
        await update.message.reply_text(
            "todavía no has enviado ningún obsequio."
        )
        return

    premios = sorted(
        set(premio for _, premio in filas),
        reverse=True
    )

    mensaje = "๑ último obsequio\n\n"

    emojis = ["🐰", "🌸", "🍀"]

    for i, premio in enumerate(premios):

        emoji = emojis[i] if i < len(emojis) else "✨"

        mensaje += f"{emoji} premio ({premio} kooins)\n"

        for username, valor in filas:
            if valor == premio:
                mensaje += f"• {username}\n"

        mensaje += "\n"

    mensaje += f"๑ participantes: {len(filas)}"

    await update.message.reply_text(mensaje)

# --- KOALA PERDIDO (solo admin) ---

async def koala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        await update.message.reply_text(
            "¡alto ahí! este comando solo lo puede usar la admin. 🐨"
        )
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "usa el formato:\n/koala <cantidad>"
        )
        return

    try:
        premio = int(context.args[0])

        if premio <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "el premio debe ser un número entero mayor que 0."
        )
        return

    if not KOALA_CHAT_ID:
        await update.message.reply_text(
            "⚠️ grupo no disponible para jugar."
        )
        return

    # Crear el evento del koala
    cur.execute("""
        CREATE TABLE IF NOT EXISTS koala_evento (
            id SERIAL PRIMARY KEY,
            premio INTEGER NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            ganador_id BIGINT
        )
    """)
    conn.commit()

    # Comprobar que no haya otro koala activo
    cur.execute("""
        SELECT id
        FROM koala_evento
        WHERE activo = TRUE
        LIMIT 1
    """)

    if cur.fetchone():
        await update.message.reply_text(
            "ya hay un koala perdido en el grupo.. 🐨"
        )
        return

    cur.execute("""
        INSERT INTO koala_evento (premio, activo)
        VALUES (%s, TRUE)
    """, (premio,))

    conn.commit()

    cur.execute("""
        SELECT id
        FROM koala_evento
        WHERE activo = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    evento_id = cur.fetchone()[0]

    keyboard = [
        [InlineKeyboardButton(
            "🐨 ‹𝟹",
            callback_data=f"koala:{evento_id}"
        )]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar koala con imagen
    await context.bot.send_photo(
        chat_id=int(KOALA_CHAT_ID),
        photo=open("koala.jpg", "rb"),
        caption=(
            "⠀⠀⠀⠀۫ ׅ ¡KOALA PERDIDO! ੭﹕﹒\n"
            "Oh, parece que el koala se ha escapado y quiso visitar el grupo..\n\n"
            "¡Atrápalo antes que los demás! ₍₍⚞(˶>ᗜ<˶)⚟⁾⁾"
        ),
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        f"🐨 ¡Koala enviado al grupo!\n"
        f"Premio secreto: {premio} kooins."
    )

async def atrapar_koala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    # Bloqueados no pueden ganar
    if user_id in BLOQUEADOS:
        return

    evento_id = int(query.data.split(":")[1])

    # Intentamos cerrar el evento.
    # Solo el primero que lo haga con éxito será el ganador.
    cur.execute("""
        UPDATE koala_evento
        SET activo = FALSE,
            ganador_id = %s
        WHERE id = %s
          AND activo = TRUE
        RETURNING premio
    """, (user_id, evento_id))

    row = cur.fetchone()

    if not row:
        await query.answer(
            "(｡ᵕ ◞ _◟) ¡muy tarde! alguien ya atrapó el koala.",
            show_alert=True
        )
        return

    premio = row[0]

    username = (
        f"@{query.from_user.username}"
        if query.from_user.username
        else query.from_user.first_name
    )

    # Sumar los kooins al ranking
    cur.execute("""
        INSERT INTO puntos (user_id, username, score)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET score = puntos.score + EXCLUDED.score,
            username = EXCLUDED.username
    """, (user_id, username, premio))

    conn.commit()

    # Cambiar el texto de la imagen por el resultado
    await query.edit_message_caption(
        caption=(
            f"๋࣭ ⭑ ¡{username} lo ha atrapado!\n"
            f"¡Ha ganado {premio} kooins! (๑>؂•̀๑)"
        )
    )

# --- CANCELAR KOALA (solo admin) ---

async def cancelarkoala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        await update.message.reply_text(
            "este comando es solo para la admin. 🐨"
        )
        return

    cur.execute("""
        UPDATE koala_evento
        SET activo = FALSE
        WHERE activo = TRUE
    """)

    conn.commit()

    await update.message.reply_text(
        "୨ৎ koala cancelado.\n"
        "ya puedes iniciar otro cuando quieras. ✿"
    )

# --- HANDLER PARA "." ---
async def texto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = str(update.effective_user.id)
    if user_id in BLOQUEADOS:
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

# --- RIFA (solo admin) ---
async def rifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        await update.message.reply_text(
            "¡solo los admin autorizados pueden iniciar una rifa!"
        )
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            "usa el formato:\n"
            "/rifa <kooins> <robux> <numeros>\n\n"
            "ejemplo:\n"
            "/rifa 30 20 10"
        )
        return

    try:
        costo = int(context.args[0])
        robux = int(context.args[1])
        cantidad = int(context.args[2])

        if costo <= 0 or robux <= 0 or cantidad <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "los tres valores deben ser números enteros mayores que 0."
        )
        return

    # Comprobar si ya hay una rifa activa
    cur.execute("""
        SELECT id
        FROM rifas
        WHERE activa = TRUE
        LIMIT 1
    """)

    if cur.fetchone():
        await update.message.reply_text(
            "ya hay una rifa activa. ( – ⌓ – )\n"
            "termina esa antes de iniciar otra."
        )
        return

    # Crear la nueva rifa
    cur.execute("""
        INSERT INTO rifas
        (costo_kooins, premio_robux, cantidad_numeros, activa)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
    """, (costo, robux, cantidad))

    rifa_id = cur.fetchone()[0]

    conn.commit()

    await update.message.reply_text(
        "⠀⠀⠀ ⠀ ⠀⠀NAM'S LUCKY NUMBER ♡ˎˊ˗\n\n"
        "⠀⠀ ⠀⠀ ୨ৎ ¡nueva rifa abierta!\n\n"
        f"⠀⠀⠀🎟️ valor entrada: {costo} kooins\n"
        f"⠀⠀⠀🐨 premio: {robux} robux\n"
        f"⠀⠀⠀⋆ . números disponibles:{cantidad}\n\n"
        "presiona el botón para conseguir tu número. ੭﹕"
    )

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
app.add_handler(CallbackQueryHandler(
    atrapar_koala,
    pattern=r"^koala:"
))
app.add_handler(CallbackQueryHandler(elegir_bolsa))
app.add_handler(CommandHandler("kooins", kooins))
app.add_handler(CommandHandler("obsequio", obsequio))
app.add_handler(CommandHandler("verobsequio", verobsequio))
app.add_handler(CommandHandler("rifa", rifa))
app.add_handler(CommandHandler("koala", koala))
app.add_handler(CommandHandler("cancelarkoala", cancelarkoala))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_handler))

# Aquí cambias polling por webhook
app.run_webhook(
    listen="0.0.0.0",
    port=8000,
    url_path=TOKEN,
    webhook_url=f"https://bot-telegram-2-lcx9.onrender.com/{TOKEN}"
)
