#!/usr/bin/env python
import logging
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from kerykeion import Report, AstrologicalSubject
import requests, asyncio

# Habilitar logging en archivo
logging.basicConfig(filename='actividad_del_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes para etapas de la conversación
(NOMBRE, AÑO, MES, DIA, HORA, UBICACION, RESULTADO, REPETIR) = range(8)

# Claves de API
TELEGRAM_TOKEN = "7005636792:AAFsRSBKvxA67FoQao1f7AdjPxYKvwk9cvY"
OPENAI_API_KEY = "sk-proj-qB50VcbkJBZdzm5dXV9PT3BlbkFJBAK619TeTVNu76CPHaM8"

# Funciones auxiliares
def quitar_ceros_inicio(numero_str):
    try:
        return str(int(numero_str))
    except ValueError:
        return None

def validar_hora(hora_str):
    try:
        hora, minuto = map(int, hora_str.split(":"))
        if 0 <= hora <= 23 and 0 <= minuto <= 59:
            return hora, minuto
        else:
            return None, None
    except ValueError:
        return None, None

def crear_carta_astral(nombre, año, mes, dia, hora, minuto, ubicacion):
    try:
        logger.info(f"Creando carta astral para {nombre}, {año}-{mes}-{dia}, {hora}:{minuto}, {ubicacion}")
        sujeto = AstrologicalSubject(nombre, int(año), int(mes), int(dia), int(hora), int(minuto), ubicacion)
        informe = Report(sujeto)
        informe_completo = informe.get_full_report()
        return formatear_carta(informe_completo)
    except Exception as e:
        logger.error(f"Error al crear la carta astral: {e}")
        return None

def formatear_carta(carta):
    if not carta:
        return "Error al generar la carta astral."
    
    parte_interes = carta.split("Date")[1]
    lineas = parte_interes.split('\n')
    lineas_formateadas = []
    for linea in lineas:
        linea = linea.replace('+', '-')
        if '-' in linea:
            linea = linea[:57]
        lineas_formateadas.append(linea)
    return "🌟----------------------------------------🌟\nDate" + '\n'.join(lineas_formateadas)

def obtener_prediccion_astrologica(nombre, ubicacion, carta):
    try:
        endpoint = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }
        prompt = f"""
        🌟🔮 Tú eres una bruja hábil en leer a las personas. Aquí está la carta astral de alguien especial. Basándote en ella, realiza una lectura profunda sobre esta persona. Sumérgete en aspectos clave como pasatiempos, familia, trabajo y vida amorosa. Recuerda, eres una bruja astuta y hábil, capaz de hacer afirmaciones muy precisas con absoluta certeza:

        {carta}

        🧙‍♀️ El nombre de la persona es {nombre}. Háblale a {nombre} en segunda persona, como si le estuvieras hablando directamente. No menciones la carta astral directamente; úsala solo como guía en tus predicciones. Imagina sus pasatiempos y lo que más valora en la vida cotidiana. Considera su posible edad (GenZ o Millennial) y género (determina por el nombre), así como su origen de {ubicacion}. Usa muchos emojis en la respuesta, uno o dos por párrafo, haciéndolos relevantes a lo que estás diciendo. 🌌✨
        """
        data = {
            'model': 'gpt-4o',
            'messages': [{'role': 'system', 'content': 'Eres una experta bruja en leer a las personas a través de sus cartas astrales. Usa tu habilidad para revelar detalles precisos y profundos sobre sus vidas, intereses y personalidades.'},
                         {'role': 'user', 'content': prompt}]
        }
        response = requests.post(endpoint, headers=headers, json=data)
        respuesta_prediccion = response.json()
        contenido = respuesta_prediccion['choices'][0]['message']['content']
        return contenido
    except Exception as e:
        logger.error(f"Error al obtener la predicción astrológica: {e}")
        return "Error al obtener la predicción astrológica."

def registrar_interaccion_usuario(context):
    with open("usuarios.txt", "a") as archivo:
        datos_usuario = context.user_data
        archivo.write(f"Nombre: {datos_usuario.get('nombre', 'Desconocido')}\n")
        archivo.write(f"Fecha: {datos_usuario.get('dia', 'DD')}-{datos_usuario.get('mes', 'MM')}-{datos_usuario.get('año', 'AAAA')}\n")
        archivo.write(f"Hora: {datos_usuario.get('hora', 'HH')}:{datos_usuario.get('minuto', 'MM')}\n")
        archivo.write(f"Ubicación: {datos_usuario.get('ubicacion', 'Desconocida')}\n")
        archivo.write("-------------------------------\n")

# Funciones de manejo de comandos
async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🌙✨ ¡Saludos! Soy la Urubruja, nacida en los místicos paisajes de Cabo Polonio. ¿Cuál es tu nombre, alma curiosa?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NOMBRE

async def nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nombre = update.message.text.strip()
    if len(nombre) > 40:
        await update.message.reply_text("🔮 Tu nombre parece ser muy largo, ¿puedes darme uno más corto?")
        return NOMBRE
    context.user_data["nombre"] = nombre
    await update.message.reply_text("🌟 Un placer conocerte, ¿en qué año (AAAA) cruzaste por primera vez el umbral del tiempo?")
    return AÑO

async def año(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    año = quitar_ceros_inicio(update.message.text)
    if año is not None and 1900 <= int(año) <= 2027:
        context.user_data["año"] = año
        await update.message.reply_text("📅 Ahora dime, ¿en qué mes (MM) te vio nacer el sol por primera vez?")
        return MES
    else:
        await update.message.reply_text("⏳ Ese año no parece válido, por favor intenta con otro.")
        return AÑO

async def mes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mes = quitar_ceros_inicio(update.message.text)
    if mes is not None and 1 <= int(mes) <= 12:
        context.user_data["mes"] = mes
        await update.message.reply_text("🌒 Interesante, ¿y en qué día (DD) despertaste a este mundo?")
        return DIA
    else:
        await update.message.reply_text("📆 Ese mes no parece válido, por favor intenta con otro.")
        return MES

async def dia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dia = quitar_ceros_inicio(update.message.text)
    if dia is not None and 1 <= int(dia) <= 31:
        context.user_data["dia"] = dia
        await update.message.reply_text("⏰ ¿A qué hora comenzó a fluir tu magia? Dime la hora en formato HH:MM (24h)")
        return HORA
    else:
        await update.message.reply_text("🗓️ Ese día no parece válido, por favor intenta con otro.")
        return DIA

async def hora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hora, minuto = validar_hora(update.message.text)
    if hora is not None:
        context.user_data["hora"] = hora
        context.user_data["minuto"] = minuto
        await update.message.reply_text("🌍 Fascinante, ¿cuál es el lugar de poder donde tu esencia fue invocada por primera vez? (Indica la ciudad importante más cercana)")
        return UBICACION
    else:
        await update.message.reply_text("⌛ Asegúrate de usar el formato correcto HH:MM.")
        return HORA

async def ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ubicacion = update.message.text.strip()
    if len(ubicacion) <= 50:
        context.user_data["ubicacion"] = ubicacion
        logger.info(f"Ubicación recibida: {ubicacion}")
        carta = crear_carta_astral(context.user_data["nombre"], context.user_data["año"],
                                   context.user_data["mes"], context.user_data["dia"],
                                   context.user_data["hora"], context.user_data["minuto"],
                                   context.user_data["ubicacion"])
        if carta:
            await update.message.reply_text(f"🌌 ¡Aquí está tu carta astral, revelada ante mis ojos!\n{carta}")
            await update.message.reply_text("🔮 Dame un momento mientras consulto las estrellas y tejo tu predicción...")
            prediccion = obtener_prediccion_astrologica(context.user_data["nombre"], context.user_data["ubicacion"], carta)
            
            await update.message.reply_text("⭐ Con las estrellas como testigo, aquí está tu predicción:")
            await asyncio.sleep(2)  # Pausa de 2 segundos para suspense

            parrafos_prediccion = prediccion.split('\n')
            for parrafo in parrafos_prediccion:
                if parrafo.strip():  # Solo enviar párrafos no vacíos
                    await update.message.reply_text(parrafo)
                    await asyncio.sleep(7)  # Pausa de 7 segundos entre párrafos

            registrar_interaccion_usuario(context)  # Registrar la interacción del usuario
            await asyncio.sleep(10)  # Pausa de 10 segundos antes de preguntar si desean continuar
            await update.message.reply_text(
                '🌟 ¡Espero que mis palabras resuenen contigo! ¿Te gustaría seguir preguntando sobre otras almas de las que desees saber más?'
            )
            return REPETIR
        else:
            await update.message.reply_text("⚠️ Hubo un error al generar tu carta astral. Por favor, intenta de nuevo más tarde.")
            return ConversationHandler.END
    else:
        await update.message.reply_text("🌆 Ese lugar parece demasiado largo, ¿puedes indicar una ciudad importante más cercana?")
        return UBICACION

async def preguntar_repetir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    teclado_respuesta = [['Sí', 'No']]
    await update.message.reply_text(
        '🌟 ¡Espero que mis palabras resuenen contigo! ¿Te gustaría seguir preguntando sobre otras almas de las que desees saber más?',
        reply_markup=ReplyKeyboardMarkup(teclado_respuesta, one_time_keyboard=True, input_field_placeholder='¿Sí o No?')
    )
    return REPETIR

async def repetir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text
    if respuesta.lower().startswith('s'):
        await update.message.reply_text("🌠 ¡Maravilloso! ¿Cuál es el nombre de esta nueva alma?")
        return NOMBRE
    else:
        await update.message.reply_text("✨ Lamentablemente, nuestros caminos se separan. ¡Espero que nuestras sendas se crucen nuevamente!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('✨ Lamentablemente, nuestros caminos se separan. ¡Espero que nuestras sendas se crucen nuevamente!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
         entry_points=[
            CommandHandler('start', inicio),  # Se activa con el comando /start
            MessageHandler(filters.TEXT & ~filters.COMMAND, inicio)  # Se activa con cualquier texto
        ],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nombre)],
            AÑO: [MessageHandler(filters.TEXT & ~filters.COMMAND, año)],
            MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, mes)],
            DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, dia)],
            HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hora)],
            UBICACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ubicacion)],
            REPETIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, repetir)]
        },
        fallbacks=[CommandHandler("cancel", cancelar)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
