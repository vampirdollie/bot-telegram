from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import datetime, os, random
from zoneinfo import ZoneInfo
import psycopg2

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
KOALA_CHAT_ID = os.getenv("KOALA_CHAT_ID")
RIFA_CHAT_ID = os.getenv("RIFA_CHAT_ID")
ZONA_COLOMBIA = ZoneInfo("America/Bogota")

SUPERADMINS = ["7943521525"]  # solo tú
MAX_INTENTOS_RIESGO = 3

# --- Bloqueados ---
BLOQUEADOS = [
    "6378265355", # liss
    "5353963160", # ali
    "5760026959", # lia
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

    username = (
        f"@{query.from_user.username}"
        if query.from_user.username
        else f"ID:{user_id}"
    )

    premio = int(query.data)

    cur.execute("""
        INSERT INTO puntos (user_id, username, score)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET score = puntos.score + EXCLUDED.score,
            username = EXCLUDED.username
    """, (user_id, username, premio))

    # Registrar movimiento en bankooins
    cur.execute("""
        INSERT INTO movimientos_kooins
        (user_id, cantidad, tipo)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        premio,
        "juego_diario"
    ))

    conn.commit()

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

    # Reiniciar historial de Bankooins
    cur.execute("DELETE FROM movimientos_kooins")

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
        await update.message.reply_text(
            "¡alto ahí, velocista! este comando solo lo puede usar la admin."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "usa el formato:\n"
            "/kooins <cantidad> @usuario\n\n"
            "ejemplos:\n"
            "/kooins 50 @usuario → sumar 50 kooins\n"
            "/kooins -20 @usuario → restar 20 kooins"
        )
        return

    try:
        cantidad = int(context.args[0])
        objetivo = context.args[1]

        if cantidad == 0:
            await update.message.reply_text(
                "la cantidad no puede ser 0."
            )
            return

        if objetivo.startswith("@"):
            # Buscar el user_id real usando el username
            cur.execute(
                "SELECT user_id, score FROM puntos WHERE username=%s",
                (objetivo,)
            )

            row = cur.fetchone()

            if not row:
                await update.message.reply_text(
                    "ese usuario aún no ha jugado, "
                    "no puedo darle kooins. ૮◞ ◟ ა"
                )
                return

            target_id = row[0]
            saldo_actual = row[1]
            username = objetivo

        else:
            # Si se pasa un ID numérico directamente
            target_id = objetivo

            cur.execute(
                "SELECT score, username FROM puntos WHERE user_id=%s",
                (target_id,)
            )

            row = cur.fetchone()

            if not row:
                await update.message.reply_text(
                    "ese usuario aún no ha jugado, "
                    "no puedo modificar sus kooins. ૮◞ ◟ ა"
                )
                return

            saldo_actual = row[0]
            username = row[1] or f"ID:{objetivo}"

        # Bloqueados no pueden recibir ni perder kooins
        if esta_bloqueado(target_id):
            await update.message.reply_text(
                "no puedes modificar los kooins de este usuario."
            )
            return

        # Evitar saldo negativo
        nuevo_saldo = saldo_actual + cantidad

        if nuevo_saldo < 0:
            await update.message.reply_text(
                f"{username} tiene actualmente {saldo_actual} kooins.\n"
                f"no puedes restarle {abs(cantidad)} porque "
                "el saldo quedaría negativo."
            )
            return

        # Actualizar saldo
        cur.execute(
            """
            UPDATE puntos
            SET score = %s,
                username = %s
            WHERE user_id = %s
            """,
            (nuevo_saldo, username, target_id)
        )

        # Registrar movimiento en bankooins
        cur.execute(
            """
            INSERT INTO movimientos_kooins
            (user_id, cantidad, tipo)
            VALUES (%s, %s, %s)
            """,
            (target_id, cantidad, "admin")
        )

        conn.commit()

        if cantidad > 0:
            await update.message.reply_text(
                f"¡se sumaron {cantidad} kooins a {username}!\n"
                f"ahora tiene {nuevo_saldo} kooins. ٩(ˊᗜˋ*)و"
            )
        else:
            await update.message.reply_text(
                f"se restaron {abs(cantidad)} kooins a {username}.\n"
                f"ahora tiene {nuevo_saldo} kooins. (◞‸◟,)"
            )

    except ValueError:
        await update.message.reply_text(
            "¡ups! la cantidad debe ser un número entero.\n\n"
            "ejemplo: /kooins 50 @usuario\n"
            "o: /kooins -20 @usuario"
        )

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

        # Registrar movimiento en bankooins
        cur.execute(
            """
            INSERT INTO movimientos_kooins
            (user_id, cantidad, tipo)
            VALUES (%s, %s, %s)
            """,
            (target_id, premio, "obsequio")
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

    # Registrar movimiento en bankooins
    cur.execute("""
        INSERT INTO movimientos_kooins
        (user_id, cantidad, tipo)
        VALUES (%s, %s, %s)
    """, (user_id, premio, "koala"))

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

    # Botón para conseguir número
    keyboard = [
        [
            InlineKeyboardButton(
                "˗ˏˋ ꒰ 🎟️ ꒱ ˎˊ˗",
                callback_data="participar_rifa"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar la rifa al grupo
    if not RIFA_CHAT_ID:
        await update.message.reply_text(
            "grupo de rifas no configurado."
        )
        return

    await context.bot.send_message(
        chat_id=int(RIFA_CHAT_ID),
        text=(
            "⠀⠀\n"
            "⠀⠀⠀𝗡𝗔𝗠'𝗦 𝗟𝗨𝗖𝗞𝗬 𝗡𝗨𝗠𝗕𝗘𝗥 𖹭\n\n"
            "⠀⠀ ⠀⠀ ୨ৎ ¡nueva rifa abierta!\n\n"
            f"⠀⠀⠀🎟️ valor entrada: {costo} kooins\n"
            f"⠀⠀⠀🐨 premio: {robux} robux\n"
            f"⠀⠀⠀⋆ . números disponibles: {cantidad}\n\n"
            "presiona el botón para conseguir tu número. ੭﹕"
        ),
        reply_markup=reply_markup
    )

    # Confirmación privada para la admin
    await update.message.reply_text(
        "¡rifa enviada al grupo! 🎟️"
    )

# --- PARTICIPAR EN RIFA ---
async def participar_rifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    user_id = str(query.from_user.id)

    if user_id in BLOQUEADOS:
        await query.answer(
            "no puedes participar en esta dinámica.",
            show_alert=True
        )
        return

    # Buscar la rifa activa
    cur.execute("""
        SELECT id, costo_kooins, premio_robux, cantidad_numeros
        FROM rifas
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    rifa_actual = cur.fetchone()

    if not rifa_actual:
        await query.answer(
            "no hay ninguna rifa activa ahora mismo.",
            show_alert=True
        )
        return

    rifa_id, costo, premio_robux, cantidad_numeros = rifa_actual

    # Comprobar si ya participa
    cur.execute("""
        SELECT numero
        FROM rifa_participantes
        WHERE rifa_id = %s
          AND user_id = %s
    """, (rifa_id, user_id))

    ya_participa = cur.fetchone()

    if ya_participa:
        await query.answer(
            f"ya tienes el número #{ya_participa[0]:04d}. 🐨",
            show_alert=True
        )
        return

    # Comprobar kooins
    cur.execute(
        "SELECT score FROM puntos WHERE user_id = %s",
        (user_id,)
    )

    fila_puntos = cur.fetchone()
    kooins = fila_puntos[0] if fila_puntos else 0

    if kooins < costo:
        await query.answer(
            f"necesitas {costo} kooins para participar.",
            show_alert=True
        )
        return

    # Obtener números ya ocupados
    cur.execute("""
        SELECT numero
        FROM rifa_participantes
        WHERE rifa_id = %s
    """, (rifa_id,))

    ocupados = {fila[0] for fila in cur.fetchall()}

    # La cantidad configurada es el máximo de participantes
    if len(ocupados) >= cantidad_numeros:
        await query.answer(
            "ya se ocuparon todos los números disponibles para esta rifa. 🐨",
            show_alert=True
        )
        return

    # Generar un número aleatorio entre 0001 y 9999
    disponibles = [
        numero
        for numero in range(1, 10000)
        if numero not in ocupados
    ]

    numero = random.choice(disponibles)

    username = (
        f"@{query.from_user.username}"
        if query.from_user.username
        else query.from_user.first_name
    )

    # Descontar kooins
    cur.execute("""
        UPDATE puntos
        SET score = score - %s
        WHERE user_id = %s
    """, (costo, user_id))

    # Registrar movimiento en bankooins
    cur.execute("""
        INSERT INTO movimientos_kooins
        (user_id, cantidad, tipo)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        -costo,
        "rifa"
    ))

    # Guardar participante
    cur.execute("""
        INSERT INTO rifa_participantes
        (rifa_id, user_id, username, numero, kooins_pagados)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        rifa_id,
        user_id,
        username,
        numero,
        costo
    ))

    conn.commit()

    await query.answer(
        f"¡tu número es #{numero:04d}! 🐨",
        show_alert=True
    )

    # Aviso en el chat donde está el botón
    try:
        await query.message.reply_text(
            f"    \n"
            f"¡koya te ha encontrado un número!\n"
            f"    ♡    {username}\n"
            f"    ❀    #{numero:04d}\n"
            f"    mucha suerte...\n"
            f"    "
        )
    except Exception:
        pass

# --- INFO RIFA (solo admin) ---
async def rifainfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar la rifa activa
    cur.execute("""
        SELECT id, costo_kooins, premio_robux, cantidad_numeros
        FROM rifas
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    rifa_actual = cur.fetchone()

    if not rifa_actual:
        await update.message.reply_text(
            "no hay ninguna rifa activa en este momento. ( – ⌓ – )"
        )
        return

    rifa_id, costo, robux, cantidad = rifa_actual

    # Buscar participantes
    cur.execute("""
        SELECT username, numero
        FROM rifa_participantes
        WHERE rifa_id = %s
        ORDER BY numero ASC
    """, (rifa_id,))

    participantes = cur.fetchall()

    mensaje = (
        "⠀⠀⠀ 𝗡𝗔𝗠'𝗦 𝗟𝗨𝗖𝗞𝗬 𝗡𝗨𝗠𝗕𝗘𝗥 𖹭\n\n"
        f"⠀⠀⠀🎟️ valor entrada: {costo} kooins\n"
        f"⠀⠀⠀🐨 premio: {robux} robux\n"
        f"⠀⠀⠀⋆ . números: {len(participantes)}/{cantidad}\n\n"
    )

    if not participantes:
        mensaje += (
            "todavía nadie ha conseguido un número.\n"
            "(,,•᷄﹏‎•᷅,,)"
        )
    else:
        for username, numero in participantes:
            mensaje += f"#{numero:04d} — {username}\n"

    await update.message.reply_text(mensaje)

# --- START RIFA (solo admin) ---
async def startrifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar la rifa activa
    cur.execute("""
        SELECT id, premio_robux
        FROM rifas
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    rifa_actual = cur.fetchone()

    if not rifa_actual:
        await update.message.reply_text(
            "no hay ninguna rifa activa. ( – ⌓ – )"
        )
        return

    rifa_id, premio_robux = rifa_actual

    # Buscar participantes
    cur.execute("""
        SELECT user_id, username, numero
        FROM rifa_participantes
        WHERE rifa_id = %s
    """, (rifa_id,))

    participantes = cur.fetchall()

    if not participantes:
        await update.message.reply_text(
            "todavía nadie ha conseguido un número.\n"
            "la rifa no puede comenzar. (,,•᷄﹏‎•᷅,,)"
        )
        return

    # Elegir un participante al azar
    ganador = random.choice(participantes)

    ganador_id, ganador_username, numero_ganador = ganador

    # Guardar ganador y cerrar la rifa
    cur.execute("""
        UPDATE rifas
        SET activa = FALSE,
            ganador_id = %s,
            ganador_username = %s
        WHERE id = %s
    """, (
        ganador_id,
        ganador_username,
        rifa_id
    ))

    # Registrar el premio de Robux
    cur.execute("""
        INSERT INTO ganadores_robux
        (user_id, username, robux)
        VALUES (%s, %s, %s)
    """, (
        ganador_id,
        ganador_username,
        premio_robux
    ))

    conn.commit()

    await update.message.reply_text(
        f"⠀⠀⠀\n"
        f"⠀⠀⠀𝗡𝗔𝗠'𝗦 𝗟𝗨𝗖𝗞𝗬 𝗡𝗨𝗠𝗕𝗘𝗥 𖹭\n"
        f"⠀⠀⠀✿ ¡el sorteo ha comenzado!\n"
        f"⠀⠀⠀⠀⠀⠀⠀⠀⠀# {numero_ganador:04d}\n\n"
        f"⠀⠀⠀๑ ¡{ganador_username} ha ganado!\n"
        f"⠀⠀⠀๑ premio: {premio_robux} robux\n"
        "⠀⠀⠀gracias por participar. (｡- .•)\n"
        f"⠀⠀⠀"
    )

# --- CANCELAR RIFA (solo admin) ---
async def cancelarrifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar la rifa activa
    cur.execute("""
        SELECT id
        FROM rifas
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    rifa_actual = cur.fetchone()

    if not rifa_actual:
        await update.message.reply_text(
            "no hay ninguna rifa activa para cancelar. (っ˕ -｡)"
        )
        return

    rifa_id = rifa_actual[0]

    # Buscar participantes y lo que pagaron
    cur.execute("""
        SELECT user_id, kooins_pagados
        FROM rifa_participantes
        WHERE rifa_id = %s
    """, (rifa_id,))

    participantes = cur.fetchall()

    # Devolver los kooins
    for participante_id, kooins_pagados in participantes:
        cur.execute("""
            UPDATE puntos
            SET score = score + %s
            WHERE user_id = %s
        """, (kooins_pagados, participante_id))

        # Registrar devolución en bankooins
        cur.execute("""
            INSERT INTO movimientos_kooins
            (user_id, cantidad, tipo)
            VALUES (%s, %s, %s)
        """, (
            participante_id,
            kooins_pagados,
            "rifa"
        ))

    # Cerrar la rifa
    cur.execute("""
        UPDATE rifas
        SET activa = FALSE
        WHERE id = %s
    """, (rifa_id,))

    conn.commit()

    await update.message.reply_text(
        "⠀⠀⠀\n"
        "๑ la rifa ha sido cancelada.\n\n"
        f" ✿ participantes reembolsados: {len(participantes)}\n"
        ". . . sus kooins fueron devueltos.\n\n"
        "ya puedes iniciar una nueva rifa cuando quieras.\n"
        "⠀⠀⠀"
    )

# --- GANADORES DE ROBUX (solo admin) ---
async def ganadoresrobux(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    cur.execute("""
        SELECT user_id, username, SUM(robux) AS total_robux
        FROM ganadores_robux
        GROUP BY user_id, username
        ORDER BY total_robux DESC
    """)

    ganadores = cur.fetchall()

    if not ganadores:
        await update.message.reply_text(
            "todavía no hay ganadores de robux. ¡admins, no sean tacaños!"
        )
        return

    mensaje = "✿ historial de ganadores:\n\n"

    total_robux = 0

    for ganador_id, username, robux in ganadores:
        mensaje += f"𖹭 {username} — {robux} robux\n"
        total_robux += robux

    mensaje += (
        f"\n"
        f"⡞⠳⣄⣀⣠⠞✿⢷\n"
        f"total entregado: {total_robux} robux"
    )

    await update.message.reply_text(mensaje)

# --- LIMPIAR RIFA (solo admin) ---
async def limpiarrifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar la rifa más reciente
    cur.execute("""
        SELECT id
        FROM rifas
        ORDER BY id DESC
        LIMIT 1
    """)

    rifa_actual = cur.fetchone()

    if not rifa_actual:
        await update.message.reply_text(
            "no hay ninguna rifa para limpiar. (っ˕ -｡)"
        )
        return

    rifa_id = rifa_actual[0]

    # Buscar participantes y lo que pagaron
    cur.execute("""
        SELECT user_id, kooins_pagados
        FROM rifa_participantes
        WHERE rifa_id = %s
    """, (rifa_id,))

    participantes = cur.fetchall()

    # Devolver los kooins
    for participante_id, kooins_pagados in participantes:
        cur.execute("""
            UPDATE puntos
            SET score = score + %s
            WHERE user_id = %s
        """, (kooins_pagados, participante_id))

        # Registrar devolución en bankooins
        cur.execute("""
            INSERT INTO movimientos_kooins
            (user_id, cantidad, tipo)
            VALUES (%s, %s, %s)
        """, (
            participante_id,
            kooins_pagados,
            "rifa"
        ))

    # Eliminar participantes
    cur.execute("""
        DELETE FROM rifa_participantes
        WHERE rifa_id = %s
    """, (rifa_id,))

    # Eliminar la rifa
    cur.execute("""
        DELETE FROM rifas
        WHERE id = %s
    """, (rifa_id,))

    # Limpiar historial de ganadores de Robux
    cur.execute("""
        DELETE FROM ganadores_robux
    """)

    conn.commit()

    await update.message.reply_text(
        "🧹 ⋮ rifas limpiada correctamente.\n\n"
        f"✿ participantes reembolsados: {len(participantes)}\n"
        "✿ sus kooins fueron devueltos.\n"
        "✿ los datos de la rifa fueron eliminados.\n"
        "✿ el historial de ganadores de Robux fue limpiado.\n\n"
        "ya puedes iniciar una nueva rifa cuando quieras. 𖹭"
    )

# --- ARRIESGAR ---
async def arriesgar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id in BLOQUEADOS:
        await mensaje_bloqueo(update)
        return

    # Comprobar formato
    if len(context.args) != 1:
        await update.message.reply_text(
            "usa el formato:\n"
            "/arriesgar <cantidad>\n\n"
            "ejemplo:\n"
            "/arriesgar 30"
        )
        return

    try:
        cantidad = int(context.args[0])

        if cantidad <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "la cantidad debe ser un número entero mayor que 0."
        )
        return

    # Comprobar kooins disponibles
    cur.execute(
        "SELECT score FROM puntos WHERE user_id = %s",
        (user_id,)
    )

    fila = cur.fetchone()
    kooins = fila[0] if fila else 0

    if kooins < cantidad:
        await update.message.reply_text(
            f"no tienes suficientes kooins.\n"
            f"tienes {kooins} y quieres arriesgar {cantidad}. (╹ -╹)?"
        )
        return

    hoy = datetime.datetime.now(ZONA_COLOMBIA).date()

    # Buscar los intentos de hoy
    cur.execute("""
        SELECT fecha, intentos, intentos_extra
        FROM riesgos
        WHERE user_id = %s
    """, (user_id,))

    fila_riesgo = cur.fetchone()

    if not fila_riesgo:
        intentos = 0
        intentos_extra = 0

        cur.execute("""
            INSERT INTO riesgos (user_id, fecha, intentos, intentos_extra)
            VALUES (%s, %s, 0, 0)
        """, (user_id, hoy))

        conn.commit()

    else:
        fecha, intentos, intentos_extra = fila_riesgo

        # Si es un nuevo día, reiniciar los intentos
        if fecha != hoy:
            intentos = 0
            intentos_extra = 0

            cur.execute("""
                UPDATE riesgos
                SET fecha = %s,
                    intentos = 0,
                    intentos_extra = 0
                WHERE user_id = %s
            """, (hoy, user_id))

            conn.commit()

    limite = MAX_INTENTOS_RIESGO + intentos_extra

    if intentos >= limite:
        await update.message.reply_text(
            "ya utilizaste todos tus intentos de hoy. puedes intentar que un admin te regale más, ludopata. ᓬ(ᵔ⤙ᵔ๑)ᕒ\n\n"
            f"límite actual: {limite} intentos.\n\n"
            "vuelve mañana para tentar tu suerte otra vez. 𖹭"
        )
        return

    username = (
        f"@{update.effective_user.username}"
        if update.effective_user.username
        else update.effective_user.first_name
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "৻(  •̀ ᗜ •́  ৻) arriesgar . .",
                callback_data=f"riesgo:{cantidad}"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⠀⠀⠀\n"
        f"⠀⠀⠀𝗞𝗢𝗬𝗔'𝗦 𝗥𝗜𝗦𝗞、୧ ‧ ₊˚ 🎱 ⋅ ☆ \n\n"
        f"⠀⠀⠀{username}, estás por arriesgar...\n"
        f"⠀⠀⠀**{cantidad} kooins**.\n\n"
        f"⠀⠀⠀puedes ganar, perder o tener suerte...\n"
        f"⠀⠀⠀¿te atreves? 𖹭\n\n"
        f"⠀⠀⠀intentos restantes: "
        f"{limite - intentos}/{limite}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# --- RESULTADO DE ARRIESGAR ---
async def resultado_riesgo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    user_id = str(query.from_user.id)

    if user_id in BLOQUEADOS:
        await query.answer(
            "no puedes participar en esta dinámica.",
            show_alert=True
        )
        return

    cantidad = int(query.data.split(":")[1])

    hoy = datetime.datetime.now(ZONA_COLOMBIA).date()

    # -----------------------------------------
    # COMPROBAR INTENTOS
    # -----------------------------------------

    cur.execute("""
        SELECT fecha, intentos, intentos_extra
        FROM riesgos
        WHERE user_id = %s
    """, (user_id,))

    fila = cur.fetchone()

    if not fila:
        await query.answer(
            "algo salió mal con tus intentos. intenta nuevamente.",
            show_alert=True
        )
        return

    fecha, intentos, intentos_extra = fila

    # Si cambió el día, reiniciar contador
    if fecha != hoy:
        intentos = 0
        intentos_extra = 0

        cur.execute("""
            UPDATE riesgos
            SET fecha = %s,
                intentos = 0,
                intentos_extra = 0
            WHERE user_id = %s
        """, (hoy, user_id))

        conn.commit()

    limite = MAX_INTENTOS_RIESGO + intentos_extra

    if intentos >= limite:
        await query.answer(
            "ya no tienes intentos disponibles hoy.",
            show_alert=True
        )
        return

    # -----------------------------------------
    # COMPROBAR SALDO ACTUAL
    # -----------------------------------------

    cur.execute(
        "SELECT score FROM puntos WHERE user_id = %s",
        (user_id,)
    )

    fila_puntos = cur.fetchone()
    saldo_antes = fila_puntos[0] if fila_puntos else 0

    if saldo_antes < cantidad:
        await query.answer(
            f"ya no tienes suficientes kooins.\n"
            f"tienes {saldo_antes} y quieres arriesgar {cantidad}.",
            show_alert=True
        )
        return

    # -----------------------------------------
    # SORTEO
    # -----------------------------------------

    resultado = random.choices(
        [
            "perder",
            "mitad",
            "recuperar",
            "ganar_mitad",
            "duplicar",
            "triple"
        ],
        weights=[
            20,  # perder todo
            15,  # perder mitad
            20,  # recuperar
            20,  # ganar mitad
            15,  # duplicar
            10   # triple
        ],
        k=1
    )[0]

    # -----------------------------------------
    # CALCULAR CUÁNTO OBTIENE
    # -----------------------------------------

    if resultado == "perder":

        obtenido = 0

        texto_resultado = (
            "que mala suerte... "
            "ni siquiera nosotros sabemos que decir al respecto. ( ´･･)ﾉ(._.`)"
        )

    elif resultado == "mitad":

        obtenido = cantidad // 2

        texto_resultado = (
            "ʕ-ᴥ-ʔ Koya se quedó con la mitad..."
        )

    elif resultado == "recuperar":

        obtenido = cantidad

        texto_resultado = (
            "bueno... recuperaste tu apuesta. "
            "no era tan interesante.. (◞‸ ◟)"
        )

    elif resultado == "ganar_mitad":

        obtenido = cantidad + (cantidad // 2)

        texto_resultado = (
            "ʕ·ᴥ·ʔ ¡Koya te dio un pequeño premio!"
        )

    elif resultado == "duplicar":

        obtenido = cantidad * 2

        texto_resultado = (
            "٩(ˊᗜˋ )و ｡ ¡qué suerte! "
            "duplicaste tu apuesta."
        )

    else:

        obtenido = cantidad * 3

        texto_resultado = (
            "𖦹 ׂ 𓈒🐇 ೀ ¡A COOKY LE AGRADAS! "
            "premio x3."
        )

    # -----------------------------------------
    # CALCULAR CAMBIO REAL
    # -----------------------------------------

    cambio = obtenido - cantidad

    saldo_despues = saldo_antes + cambio

    # -----------------------------------------
    # ACTUALIZAR SALDO
    # -----------------------------------------

    cur.execute("""
        UPDATE puntos
        SET score = %s
        WHERE user_id = %s
    """, (
        saldo_despues,
        user_id
    ))

    # Registrar movimiento en bankooins
    # Se registra únicamente el cambio real del saldo.
    cur.execute("""
        INSERT INTO movimientos_kooins
        (user_id, cantidad, tipo)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        cambio,
        "arriesgar"
    ))

    # -----------------------------------------
    # REGISTRAR INTENTO
    # -----------------------------------------

    cur.execute("""
        UPDATE riesgos
        SET intentos = intentos + 1
        WHERE user_id = %s
    """, (user_id,))

    conn.commit()

    # -----------------------------------------
    # INTENTOS RESTANTES
    # -----------------------------------------

    intentos_usados = intentos + 1
    restantes = limite - intentos_usados

    # -----------------------------------------
    # MOSTRAR RESULTADO
    # -----------------------------------------

    await query.answer()

    await query.edit_message_text(
        f"⠀⠀⠀𝗞𝗢𝗬𝗔'𝗦 𝗥𝗜𝗦𝗞、୧ ‧ ₊˚ 🎱 ⋅ ☆\n\n"
        f"⠀⠀⠀{texto_resultado}\n\n"

        f"⠀⠀⠀𖹭 saldo antes: **{saldo_antes} kooins**\n"
        f"⠀⠀⠀✿ arriesgaste: **{cantidad} kooins**\n"
        f"⠀⠀⠀✿ obtuviste: **{obtenido} kooins**\n"
        f"⠀⠀⠀𖹭 saldo después: **{saldo_despues} kooins**\n\n"

        f"⠀⠀⠀intentos restantes: "
        f"**{restantes}/{limite}**",
        parse_mode="Markdown"
    )

# --- DAR INTENTOS DE RIESGO (solo admin) ---
async def darintento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "usa el formato:\n"
            "/darintento <cantidad> @usuario\n\n"
            "ejemplo:\n"
            "/darintento 2 @usuario"
        )
        return

    try:
        cantidad = int(context.args[0])

        if cantidad <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "la cantidad de intentos debe ser un número entero mayor que 0."
        )
        return

    objetivo = context.args[1]

    if not objetivo.startswith("@"):
        await update.message.reply_text(
            "debes indicar el usuario con @.\n"
            "ejemplo: /darintento 2 @usuario"
        )
        return

    # Buscar al usuario en puntos
    cur.execute(
        "SELECT user_id, username FROM puntos WHERE username = %s",
        (objetivo,)
    )

    fila = cur.fetchone()

    if not fila:
        await update.message.reply_text(
            "este usuario todavía no está registrado en el bot. pidele que inicie y abra la cajita del día."
        )
        return

    target_id, username = fila

    if esta_bloqueado(target_id):
        await update.message.reply_text(
            "ups, no puedes dar intentos a este usuario."
        )
        return

    hoy = datetime.datetime.now(ZONA_COLOMBIA).date()

    # Buscar registro de riesgo
    cur.execute("""
        SELECT fecha, intentos, intentos_extra
        FROM riesgos
        WHERE user_id = %s
    """, (target_id,))

    fila_riesgo = cur.fetchone()

    if not fila_riesgo:

        cur.execute("""
            INSERT INTO riesgos
            (user_id, fecha, intentos, intentos_extra)
            VALUES (%s, %s, 0, %s)
        """, (
            target_id,
            hoy,
            cantidad
        ))

        intentos = 0
        intentos_extra = cantidad

    else:
        fecha, intentos, intentos_extra = fila_riesgo

        # Si es otro día, empezar nuevamente
        if fecha != hoy:

            intentos = 0
            intentos_extra = cantidad

            cur.execute("""
                UPDATE riesgos
                SET fecha = %s,
                    intentos = 0,
                    intentos_extra = %s
                WHERE user_id = %s
            """, (
                hoy,
                cantidad,
                target_id
            ))

        else:

            intentos_extra += cantidad

            cur.execute("""
                UPDATE riesgos
                SET intentos_extra = %s
                WHERE user_id = %s
            """, (
                intentos_extra,
                target_id
            ))

    conn.commit()

    limite_total = MAX_INTENTOS_RIESGO + intentos_extra
    disponibles = limite_total - intentos

    await update.message.reply_text(
        f"๑ se añadieron {cantidad} intentos a {username}.\n\n"
        f"✿ intentos disponibles hoy: {disponibles}\n"
        f"𖹭 límite total de hoy: {limite_total}"
    )

# --- VER INTENTOS DE RIESGO (solo admin) ---
async def verintentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "usa el formato:\n"
            "/verintentos @usuario"
        )
        return

    objetivo = context.args[0]

    if not objetivo.startswith("@"):
        await update.message.reply_text(
            "debes indicar el usuario con @.\n"
            "ejemplo: /verintentos @usuario"
        )
        return

    # Buscar usuario
    cur.execute(
        "SELECT user_id, username FROM puntos WHERE username = %s",
        (objetivo,)
    )

    fila = cur.fetchone()

    if not fila:
        await update.message.reply_text(
            "ese usuario todavía no está registrado en el bot."
        )
        return

    target_id, username = fila

    hoy = datetime.datetime.now(ZONA_COLOMBIA).date()

    # Buscar sus intentos
    cur.execute("""
        SELECT fecha, intentos, intentos_extra
        FROM riesgos
        WHERE user_id = %s
    """, (target_id,))

    fila_riesgo = cur.fetchone()

    # Si nunca ha usado /arriesgar
    if not fila_riesgo:
        intentos = 0
        intentos_extra = 0

    else:
        fecha, intentos, intentos_extra = fila_riesgo

        # Si el registro pertenece a otro día,
        # hoy vuelve a tener sus intentos normales.
        if fecha != hoy:
            intentos = 0
            intentos_extra = 0

    limite = MAX_INTENTOS_RIESGO + intentos_extra
    disponibles = max(0, limite - intentos)

    await update.message.reply_text(
        f"𝗞𝗢𝗬𝗔'𝗦 𝗥𝗜𝗦𝗞\n\n"
        f"usuario: {username}\n\n"
        f"𖹭 intentos usados: {intentos}\n"
        f"𖹭 intentos normales: {MAX_INTENTOS_RIESGO}\n"
        f"𖹭 intentos extra: {intentos_extra}\n"
        f"𖹭 disponibles hoy: {disponibles}\n\n"
        f"fecha: {hoy}"
    )

# --- JACKPOT (solo admin) ---
async def jackpot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Formato:
    # /jackpot <kooins_por_persona>
    # /jackpot <kooins_por_persona> <aporte_admin>

    if len(context.args) not in (1, 2):
        await update.message.reply_text(
            "usa el formato:\n"
            "/jackpot <kooins>\n"
            "o\n"
            "/jackpot <kooins> <aporte_admin>\n\n"
            "ejemplo:\n"
            "/jackpot 20\n"
            "/jackpot 20 50"
        )
        return

    try:
        costo = int(context.args[0])
        aporte_admin = int(context.args[1]) if len(context.args) == 2 else 0

        if costo < 5 or aporte_admin < 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "el aporte de cada participante debe ser de mínimo 5 kooins "
            "y el aporte de la admin no puede ser negativo."
        )
        return

    # Comprobar si ya hay un jackpot activo
    cur.execute("""
        SELECT id
        FROM jackpots
        WHERE activa = TRUE
        LIMIT 1
    """)

    if cur.fetchone():
        await update.message.reply_text(
            "ya hay un jackpot abierto. ⊹ ࣪ ˖\n"
            "termina ese antes de comenzar otro."
        )
        return

    # Crear el jackpot
    cur.execute("""
        INSERT INTO jackpots
        (costo_kooins, aporte_admin, pozo, activa)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
    """, (
        costo,
        aporte_admin,
        aporte_admin
    ))

    jackpot_id = cur.fetchone()[0]

    conn.commit()

    # Botón
    keyboard = [
        [
            InlineKeyboardButton(
                "guardar kooins . .",
                callback_data="participar_jackpot"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar el mensaje al grupo
    if not RIFA_CHAT_ID:
        await update.message.reply_text(
            "no hay un grupo configurado para el jackpot."
        )
        return

    await context.bot.send_message(
        chat_id=int(RIFA_CHAT_ID),
        text=(
            "⠀⠀⠀\n"
            "⠀⠀⠀ ⏔⏔ ꒰ 𝗖𝗢𝗢𝗞𝗬'𝗦 𝗝𝗔𝗖𝗞𝗣𝗢𝗧 ꒱ ⏔⏔\n\n"
            "⠀⠀⠀ el pozo ha sido abierto...\n\n"
            f"⠀⠀⠀🎟️ entrada: {costo} kooins\n"
            f"⠀⠀⠀🐰ྀི coortesía: {aporte_admin} kooins\n\n"
            f"⠀⠀⠀๑ pozo actual: {aporte_admin} kooins\n"
            "⠀⠀⠀cada personita tiene una entrada.\n"
            "⠀⠀¿te atreves a dejar tu fortuna aquí? 𖹭"
        ),
        reply_markup=reply_markup
    )

    # Confirmación privada para la admin
    await update.message.reply_text(
        "🎰 ᛝ jackpot enviado al grupo. 𖹭"
    )

# --- PARTICIPAR EN JACKPOT ---
async def participar_jackpot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id in BLOQUEADOS:
        await query.answer(
            "no puedes participar en esta dinámica.",
            show_alert=True
        )
        return

    # Buscar jackpot activo
    cur.execute("""
        SELECT id, costo_kooins, aporte_admin, pozo
        FROM jackpots
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    jackpot_actual = cur.fetchone()

    if not jackpot_actual:
        await query.answer(
            "no hay ningún jackpot activo ahora mismo. ★",
            show_alert=True
        )
        return

    jackpot_id, costo, aporte_admin, pozo = jackpot_actual

    # Comprobar si ya participa
    cur.execute("""
        SELECT id
        FROM jackpot_participantes
        WHERE jackpot_id = %s
          AND user_id = %s
    """, (jackpot_id, user_id))

    if cur.fetchone():
        await query.answer(
            "ya tienes una entrada en este jackpot. ★",
            show_alert=True
        )
        return

    # Comprobar kooins disponibles
    cur.execute(
        "SELECT score FROM puntos WHERE user_id = %s",
        (user_id,)
    )

    fila_puntos = cur.fetchone()
    kooins = fila_puntos[0] if fila_puntos else 0

    if kooins < costo:
        await query.answer(
            f"necesitas {costo} kooins para entrar.\n"
            f"tienes {kooins}.",
            show_alert=True
        )
        return

    username = (
        f"@{query.from_user.username}"
        if query.from_user.username
        else query.from_user.first_name
    )

    # Descontar kooins
    cur.execute("""
        UPDATE puntos
        SET score = score - %s
        WHERE user_id = %s
    """, (costo, user_id))

    # Registrar movimiento en bankooins
    cur.execute("""
        INSERT INTO movimientos_kooins
        (user_id, cantidad, tipo)
        VALUES (%s, %s, %s)
    """, (
        user_id,
        -costo,
        "jackpot"
    ))

    # Registrar participante
    cur.execute("""
        INSERT INTO jackpot_participantes
        (jackpot_id, user_id, username, kooins_aportados)
        VALUES (%s, %s, %s, %s)
    """, (
        jackpot_id,
        user_id,
        username,
        costo
    ))

    # Sumar los kooins al pozo
    cur.execute("""
        UPDATE jackpots
        SET pozo = pozo + %s
        WHERE id = %s
    """, (costo, jackpot_id))

    conn.commit()

    # Obtener pozo actualizado
    cur.execute("""
        SELECT pozo
        FROM jackpots
        WHERE id = %s
    """, (jackpot_id,))

    nuevo_pozo = cur.fetchone()[0]

    # Contar participantes
    cur.execute("""
        SELECT COUNT(*)
        FROM jackpot_participantes
        WHERE jackpot_id = %s
    """, (jackpot_id,))

    participantes = cur.fetchone()[0]

    await query.answer(
        f"੭﹕¡guardaste {costo} kooins en el jackpot! 🎰",
        show_alert=True
    )

    try:
        await query.message.reply_text(
            f"⠀⠀⠀\n"
            f"⠀⠀⠀𖹭 {username} ha guardado
            f"⠀⠀⠀sus kooins en el pozo.\n\n"
            f"⠀⠀⠀🎟️ aporte: {costo} kooins\n"
            f"⠀⠀⠀๑ pozo actual: {nuevo_pozo} kooins\n"
            f"⠀⠀⠀๑ participantes: {participantes}\n\n"
            f"⠀⠀⠀una entrada asegurada...\n"
            f"⠀⠀⠀mucha suerte. 𖹭"
        )
    except Exception:
        pass

# --- START JACKPOT (solo admin) ---
async def startjackpot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar jackpot activo
    cur.execute("""
        SELECT id, pozo
        FROM jackpots
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    jackpot_actual = cur.fetchone()

    if not jackpot_actual:
        await update.message.reply_text(
            "no hay ningún jackpot activo en este momento. ૮๑ˊ  ˋ๑ა"
        )
        return

    jackpot_id, pozo = jackpot_actual

    # Buscar participantes
    cur.execute("""
        SELECT user_id, username
        FROM jackpot_participantes
        WHERE jackpot_id = %s
    """, (jackpot_id,))

    participantes = cur.fetchall()

    if not participantes:
        await update.message.reply_text(
            "todavía nadie se ha unido al jackpot.\n"
            "no hay nadie a quien elegir. ૮๑ˊ  ˋ๑ა"
        )
        return

    # Elegir ganador al azar
    ganador = random.choice(participantes)

    ganador_id, ganador_username = ganador

    # Cerrar jackpot y guardar ganador
    cur.execute("""
        UPDATE jackpots
        SET activa = FALSE,
            ganador_id = %s,
            ganador_username = %s
        WHERE id = %s
    """, (
        ganador_id,
        ganador_username,
        jackpot_id
    ))

    # Entregar todo el pozo al ganador
    cur.execute("""
        UPDATE puntos
        SET score = score + %s
        WHERE user_id = %s
    """, (pozo, ganador_id))

    # Registrar movimiento en bankooins
    cur.execute("""
        INSERT INTO movimientos_kooins
        (user_id, cantidad, tipo)
        VALUES (%s, %s, %s)
    """, (
        ganador_id,
        pozo,
        "jackpot"
    ))

    conn.commit()

    await update.message.reply_text(
        f"⠀⠀⠀\n"
        f"⠀⠀⠀⏔⏔ ꒰ 𝗖𝗢𝗢𝗞𝗬'𝗦 𝗝𝗔𝗖𝗞𝗣𝗢𝗧 ꒱ ⏔⏔\n\n"
        f"⠀⠀⠀๑ el pozo ha encontrado un ganador...\n\n"
        f"⠀⠀⠀𖹭 {ganador_username}\n\n"
        f"⠀⠀⠀๑ premio: {pozo} kooins\n"
        f"⠀⠀⠀¡todo el pozo es tuyo!\n"
        f"⠀⠀⠀qué suerte tan bonita. 𖹭"
    )

# --- CANCELAR JACKPOT (solo admin) ---
async def cancelarjackpot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in SUPERADMINS:
        return

    # Buscar jackpot activo
    cur.execute("""
        SELECT id
        FROM jackpots
        WHERE activa = TRUE
        ORDER BY id DESC
        LIMIT 1
    """)

    jackpot_actual = cur.fetchone()

    if not jackpot_actual:
        await update.message.reply_text(
            "no hay ningún jackpot activo para cancelar. (っ˕ -｡)"
        )
        return

    jackpot_id = jackpot_actual[0]

    # Buscar participantes y sus aportes
    cur.execute("""
        SELECT user_id, kooins_aportados
        FROM jackpot_participantes
        WHERE jackpot_id = %s
    """, (jackpot_id,))

    participantes = cur.fetchall()

    # Devolver los kooins
    for participante_id, kooins_aportados in participantes:

        cur.execute("""
            UPDATE puntos
            SET score = score + %s
            WHERE user_id = %s
        """, (
            kooins_aportados,
            participante_id
        ))

        # Registrar devolución en bankooins
        cur.execute("""
            INSERT INTO movimientos_kooins
            (user_id, cantidad, tipo)
            VALUES (%s, %s, %s)
        """, (
            participante_id,
            kooins_aportados,
            "jackpot"
        ))

    # Cerrar el jackpot
    cur.execute("""
        UPDATE jackpots
        SET activa = FALSE
        WHERE id = %s
    """, (jackpot_id,))

    conn.commit()

    await update.message.reply_text(
        "⠀⠀⠀\n"
        "⠀⠀⠀ ⏔⏔ ꒰ 𝗖𝗢𝗢𝗞𝗬'𝗦 𝗝𝗔𝗖𝗞𝗣𝗢𝗧 ꒱ ⏔⏔\n\n"
        "⠀⠀⠀๑ el jackpot ha sido cancelado.\n\n"
        f"⠀⠀⠀✿ participantes reembolsados: {len(participantes)}\n"
        "⠀⠀⠀✿ sus kooins fueron devueltos.\n\n"
        "⠀⠀⠀el pozo ha quedado cerrado.\n"
        "⠀⠀⠀ya puedes iniciar otro cuando quieras. 𖹭"
    )

# --- BANKOOINS ---
async def bankooins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # ==========================================
    # CONSULTAR A OTRO USUARIO (SOLO ADMIN)
    # ==========================================

    if len(context.args) == 1:

        if user_id not in SUPERADMINS:
            await update.message.reply_text(
                "solo los admins pueden consultar los bankooins de otros usuarios."
            )
            return

        objetivo = context.args[0]

        if not objetivo.startswith("@"):
            await update.message.reply_text(
                "debes indicar el usuario con @.\n"
                "ejemplo: /bankooins @usuario"
            )
            return

        cur.execute(
            """
            SELECT user_id, username, score
            FROM puntos
            WHERE username = %s
            """,
            (objetivo,)
        )

        fila = cur.fetchone()

        if not fila:
            await update.message.reply_text(
                "ese usuario todavía no está registrado en el bot."
            )
            return

        target_id, username, saldo_actual = fila

    # ==========================================
    # CONSULTAR LOS PROPIOS BANKOOINS
    # ==========================================

    elif len(context.args) == 0:

        target_id = user_id

        cur.execute(
            """
            SELECT username, score
            FROM puntos
            WHERE user_id = %s
            """,
            (target_id,)
        )

        fila = cur.fetchone()

        if not fila:
            await update.message.reply_text(
                "(っ˕ -｡) 𝗓 𐰁 Aún no tienes kooins registrados."
            )
            return

        username, saldo_actual = fila

    # ==========================================
    # FORMATO INCORRECTO
    # ==========================================

    else:

        await update.message.reply_text(
            "usa el formato:\n"
            "/bankooins\n\n"
            "o, si eres admin:\n"
            "/bankooins @usuario"
        )
        return

    # ==========================================
    # BUSCAR HISTORIAL
    # ==========================================

    cur.execute(
        """
        SELECT cantidad, tipo, fecha
        FROM movimientos_kooins
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (target_id,)
    )

    movimientos = cur.fetchall()

    mensaje = (
        f"⠀⠀⠀ ꒰ 𝗕𝗔𝗡𝗞𝗢𝗢𝗜𝗡𝗦 ꒱\n\n"
        f"𖹭 usuario: {username}\n"
        f"𖹭 saldo actual: {saldo_actual} kooins\n\n"
    )

    if not movimientos:

        mensaje += (
            "⠀⠀⠀⏤⏤⏤⏤⏤\n\n"
            "✿ todavía no tiene movimientos registrados."
        )

    else:

        mensaje += (
            "⠀⠀⠀⏤⏤⏤⏤⏤\n\n"
            "✿ historial de movimientos:\n\n"
        )

        ganados = 0
        gastados = 0

        for cantidad, tipo, fecha in movimientos:

            signo = "+" if cantidad > 0 else ""

            if cantidad > 0:
                ganados += cantidad
            else:
                gastados += cantidad

            fecha_formateada = fecha.strftime(
                "%d/%m/%Y %H:%M"
            )

            mensaje += (
                f"𖹭 {signo}{cantidad} kooins\n"
                f"   └ {tipo} · {fecha_formateada}\n"
            )

        mensaje += (
            "⠀⠀⠀⏤⏤⏤⏤⏤\n\n"
            f"✿ kooins ganados: +{ganados}\n"
            f"✿ kooins gastados: {gastados}\n"
            f"✿ saldo actual: {saldo_actual} kooins"
        )

    await update.message.reply_text(mensaje)

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
app.add_handler(
    CallbackQueryHandler(
        participar_rifa,
        pattern=r"^participar_rifa$"
    )
)
app.add_handler(
    CallbackQueryHandler(
        resultado_riesgo,
        pattern=r"^riesgo:"
    )
)
app.add_handler(
    CallbackQueryHandler(
        participar_jackpot,
        pattern=r"^participar_jackpot$"
    )
)
app.add_handler(CallbackQueryHandler(elegir_bolsa))
app.add_handler(CommandHandler("kooins", kooins))
app.add_handler(CommandHandler("obsequio", obsequio))
app.add_handler(CommandHandler("verobsequio", verobsequio))
app.add_handler(CommandHandler("rifa", rifa))
app.add_handler(CommandHandler("rifainfo", rifainfo))
app.add_handler(CommandHandler("startrifa", startrifa))
app.add_handler(CommandHandler("cancelarrifa", cancelarrifa))
app.add_handler(CommandHandler("limpiarrifa", limpiarrifa))
app.add_handler(CommandHandler("ganadoresrobux", ganadoresrobux))
app.add_handler(CommandHandler("koala", koala))
app.add_handler(CommandHandler("cancelarkoala", cancelarkoala))
app.add_handler(CommandHandler("arriesgar", arriesgar))
app.add_handler(CommandHandler("darintento", darintento))
app.add_handler(CommandHandler("verintentos", verintentos))
app.add_handler(CommandHandler("jackpot", jackpot))
app.add_handler(CommandHandler("startjackpot", startjackpot))
app.add_handler(CommandHandler("cancelarjackpot", cancelarjackpot))
app.add_handler(CommandHandler("bankooins", bankooins))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_handler))

app.run_webhook(
    listen="0.0.0.0",
    port=8000,
    url_path=TOKEN,
    webhook_url=f"https://bot-telegram-2-lcx9.onrender.com/{TOKEN}"
)
