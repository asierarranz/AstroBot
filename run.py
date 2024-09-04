#!/usr/bin/env python
import logging
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from kerykeion import Report, AstrologicalSubject, KerykeionChartSVG
import requests, asyncio, unicodedata, os, time
import os
from dotenv import load_dotenv
load_dotenv()

# Enable logging to a file
logging.basicConfig(filename='bot_activity.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for conversation stages
(NAME, YEAR, MONTH, DAY, TIME, LOCATION, COUNTRY_CODE, RESULT, REPEAT) = range(9)

# API keys
telegram_token = os.getenv('TELEGRAM_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')

# Arrays of main cities
ARGENTINA_CITIES = ["buenos aires", "cordoba", "rosario", "mendoza", "la plata", "san miguel de tucuman", "mar del plata", "salta", "santa fe", "san juan"]
SPAIN_CITIES = ["madrid", "barcelona", "valencia", "sevilla", "zaragoza", "malaga", "murcia", "palma", "las palmas", "bilbao"]

def normalize_string(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# Auxiliary functions
def strip_leading_zeros(number_str):
    try:
        return str(int(number_str))
    except ValueError:
        return None

def validate_time(time_str):
    try:
        hour, minute = map(int, time_str.split(":"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
        else:
            return None, None
    except ValueError:
        return None, None

def create_astrological_chart(name, year, month, day, hour, minute, location, country_code):
    try:
        logger.info(f"Creating astrological chart for {name}, {year}-{month}-{day}, {hour}:{minute}, {location}, {country_code}")
        subject = AstrologicalSubject(
            name,
            int(year),
            int(month),
            int(day),
            int(hour),
            int(minute),
            location,
            country_code
        )
        report = Report(subject)
        full_report = report.get_full_report()
        
        # Create SVG chart
        natal_chart = KerykeionChartSVG(subject, theme="dark", chart_language="ES")
        natal_chart.makeSVG()
        
        return format_chart(full_report)
    except Exception as e:
        logger.error(f"Error creating astrological chart: {e}")
        return None

def format_chart(chart):
    if not chart:
        return "Error generating astrological chart."
    
    part_of_interest = chart.split("Date")[1]
    lines = part_of_interest.split('\n')
    formatted_lines = []
    for line in lines:
        line = line.replace('+', '-')
        if '-' in line:
            line = line[:57]
        formatted_lines.append(line)
    return "🌟----------------------------------------🌟\nDate" + '\n'.join(formatted_lines)

def get_astrological_prediction(name, location, chart):
    try:
        endpoint = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }
        prompt = f"""
        🌟🔮 Eres una astróloga experta en leer a las personas. Aquí tienes la carta astral de alguien especial. Basándote en ella, proporciona una lectura profunda sobre esta persona. Profundiza en aspectos clave como hobbies, familia, trabajo y vida amorosa. Recuerda, eres una astróloga hábil y experta, capaz de hacer afirmaciones muy precisas con absoluta certeza:

        {chart}

        🧙‍♀️ El nombre de la persona es {name}. Háblale a {name} en segunda persona, como si le estuvieras hablando directamente. No menciones la carta astral directamente; úsala solo como guía en tus predicciones. Imagina sus hobbies y lo que más valora en la vida cotidiana. Considera su posible edad (GenZ o Millennial) y género (determinado por el nombre), así como su origen de {location}. Usa muchos emojis en la respuesta, uno o dos por párrafo, haciéndolos relevantes a lo que estás diciendo. 🌌✨
        """
        data = {
            'model': 'gpt-4',
            'messages': [{'role': 'system', 'content': 'Eres una astróloga experta en leer a las personas a través de sus cartas astrales. Usa tu habilidad para revelar detalles precisos y profundos sobre sus vidas, intereses y personalidades.'},
                         {'role': 'user', 'content': prompt}]
        }
        response = requests.post(endpoint, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        prediction_response = response.json()
        logger.info(f"OpenAI API response: {prediction_response}")
        content = prediction_response['choices'][0]['message']['content']
        return content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la solicitud: {e}")
        return "Error al obtener la predicción astrológica debido a un error en la solicitud."
    except KeyError as e:
        logger.error(f"Error de clave: {e}, contenido de la respuesta: {prediction_response}")
        return "Error al obtener la predicción astrológica debido a un error de clave."
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return "Error al obtener la predicción astrológica debido a un error inesperado."

def log_user_interaction(context):
    with open("users.txt", "a") as file:
        user_data = context.user_data
        file.write(f"Name: {user_data.get('name', 'Unknown')}\n")
        file.write(f"Date: {user_data.get('day', 'DD')}-{user_data.get('month', 'MM')}-{user_data.get('year', 'YYYY')}\n")
        file.write(f"Time: {user_data.get('hour', 'HH')}:{user_data.get('minute', 'MM')}\n")
        file.write(f"Location: {user_data.get('location', 'Unknown')}\n")
        file.write("-------------------------------\n")

# Command handling functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🌙✨ ¡Hola! Soy la A.i.stróloga, tu guía mística en el cosmos digital. Mi modelo de inteligencia artificial ha sido entrenado con todo el conocimiento ancestral humano de la astrología. ¿Cuál es tu nombre, alma curiosa?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) > 40:
        await update.message.reply_text("🔮 Tu nombre parece demasiado largo, ¿puedes darme uno más corto?")
        return NAME
    context.user_data["name"] = name
    await update.message.reply_text("🌟 Un placer conocerte, ¿en qué año (AAAA) cruzaste el umbral del tiempo por primera vez?")
    return YEAR

async def year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    year = strip_leading_zeros(update.message.text)
    if year is not None and 1900 <= int(year) <= 2027:
        context.user_data["year"] = year
        await update.message.reply_text("📅 Ahora dime, ¿en qué mes (MM) te vio nacer el sol por primera vez?")
        return MONTH
    else:
        await update.message.reply_text("⏳ Ese año no parece válido, por favor intenta con otro.")
        return YEAR

async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    month = strip_leading_zeros(update.message.text)
    if month is not None and 1 <= int(month) <= 12:
        context.user_data["month"] = month
        await update.message.reply_text("🌒 Interesante, ¿y en qué día (DD) despertaste a este mundo?")
        return DAY
    else:
        await update.message.reply_text("📆 Ese mes no parece válido, por favor intenta con otro.")
        return MONTH

async def day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    day = strip_leading_zeros(update.message.text)
    if day is not None and 1 <= int(day) <= 31:
        context.user_data["day"] = day
        await update.message.reply_text("⏰ ¿A qué hora comenzó a fluir tu magia? Dime la hora en formato HH:MM (24h)")
        return TIME
    else:
        await update.message.reply_text("🗓️ Ese día no parece válido, por favor intenta con otro.")
        return DAY

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hour, minute = validate_time(update.message.text)
    if hour is not None:
        context.user_data["hour"] = hour
        context.user_data["minute"] = minute
        await update.message.reply_text("🌍 Fascinante, ¿cuál es el lugar de poder donde tu esencia fue invocada por primera vez? (Indica la ciudad principal más cercana)")
        return LOCATION
    else:
        await update.message.reply_text("⌛ Asegúrate de usar el formato correcto HH:MM.")
        return TIME

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = normalize_string(update.message.text.strip())
    if len(location) <= 50:
        context.user_data["location"] = location
        logger.info(f"Location received: {location}")
        
        if location in ARGENTINA_CITIES:
            country_code = "AR"
        elif location in SPAIN_CITIES:
            country_code = "ES"
        else:
            await update.message.reply_text("🌍 No he encontrado tu ciudad en mi base de datos. Por favor, introduce las dos letras que indican tu país (por ejemplo, ES para España, AR para Argentina).")
            return COUNTRY_CODE
        
        context.user_data["country_code"] = country_code
        try:
            chart = create_astrological_chart(
                context.user_data["name"],
                context.user_data["year"],
                context.user_data["month"],
                context.user_data["day"],
                context.user_data["hour"],
                context.user_data["minute"],
                context.user_data["location"],
                context.user_data["country_code"]
            )
            if chart:
                await update.message.reply_text(f"🌌 ¡Aquí está tu carta astral, revelada a mis ojos!\n{chart}")
                
                # Wait for the SVG file to be created
                await asyncio.sleep(2)
                
                # Find and send the SVG file
                home_dir = os.path.expanduser("~")
                svg_files = [f for f in os.listdir(home_dir) if f.endswith('.svg')]
                if svg_files:
                    svg_path = os.path.join(home_dir, svg_files[0])
                    with open(svg_path, 'rb') as svg_file:
                        await update.message.reply_document(InputFile(svg_file))
                    os.remove(svg_path)  # Remove the SVG file after sending
                
                await update.message.reply_text("🔮 Dame un momento mientras consulto las estrellas y tejo tu predicción...")
                prediction = get_astrological_prediction(context.user_data["name"], context.user_data["location"], chart)
                
                await update.message.reply_text("⭐ Con las estrellas como testigo, aquí está tu predicción:")
                await asyncio.sleep(2)  # 2-second pause for suspense

                prediction_paragraphs = prediction.split('\n')
                for paragraph in prediction_paragraphs:
                    if paragraph.strip():  # Only send non-empty paragraphs
                        await update.message.reply_text(paragraph)
                        await asyncio.sleep(7)  # 7-second pause between paragraphs

                log_user_interaction(context)  # Log the user interaction
                await asyncio.sleep(10)  # 10-second pause before asking if they want to continue
                await update.message.reply_text(
                    '🌟 ¡Espero que mis palabras resuenen contigo! ¿Te gustaría seguir preguntando sobre otras almas que deseas conocer más?'
                )
                return REPEAT
            else:
                error_message = f"Error generating chart for: {context.user_data}"
                print(error_message)  # Debug print
                await update.message.reply_text(f"⚠️ Hubo un error al generar tu carta astral. Detalles: {error_message}")
                return ConversationHandler.END
        except Exception as e:
            error_message = f"Exception occurred: {str(e)}\nUser data: {context.user_data}"
            print(error_message)  # Debug print
            logger.error(error_message)
            await update.message.reply_text(f"⚠️ Hubo un error al generar tu carta astral. Detalles: {error_message}")
            return ConversationHandler.END
    else:
        await update.message.reply_text("🌆 Ese lugar parece demasiado largo, ¿puedes indicar una ciudad principal más cercana?")
        return LOCATION

async def country_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    country_code = update.message.text.strip().upper()
    if len(country_code) == 2:
        context.user_data["country_code"] = country_code
        try:
            chart = create_astrological_chart(
                context.user_data["name"],
                context.user_data["year"],
                context.user_data["month"],
                context.user_data["day"],
                context.user_data["hour"],
                context.user_data["minute"],
                context.user_data["location"],
                context.user_data["country_code"]
            )
            if chart:
                await update.message.reply_text(f"🌌 ¡Aquí está tu carta astral, revelada a mis ojos!\n{chart}")
                
                # Wait for the SVG file to be created
                await asyncio.sleep(2)
                
                # Find and send the SVG file
                home_dir = os.path.expanduser("~")
                svg_files = [f for f in os.listdir(home_dir) if f.endswith('.svg')]
                if svg_files:
                    svg_path = os.path.join(home_dir, svg_files[0])
                    with open(svg_path, 'rb') as svg_file:
                        await update.message.reply_document(InputFile(svg_file))
                    os.remove(svg_path)  # Remove the SVG file after sending
                
                await update.message.reply_text("🔮 Dame un momento mientras consulto las estrellas y tejo tu predicción...")
                prediction = get_astrological_prediction(context.user_data["name"], context.user_data["location"], chart)
                
                await update.message.reply_text("⭐ Con las estrellas como testigo, aquí está tu predicción:")
                await asyncio.sleep(2)  # 2-second pause for suspense

                prediction_paragraphs = prediction.split('\n')
                for paragraph in prediction_paragraphs:
                    if paragraph.strip():  # Only send non-empty paragraphs
                        await update.message.reply_text(paragraph)
                        await asyncio.sleep(7)  # 7-second pause between paragraphs

                log_user_interaction(context)  # Log the user interaction
                await asyncio.sleep(10)  # 10-second pause before asking if they want to continue
                await update.message.reply_text(
                    '🌟 ¡Espero que mis palabras resuenen contigo! ¿Te gustaría seguir preguntando sobre otras almas que deseas conocer más?'
                )
                return REPEAT
            else:
                error_message = f"Error generating chart for: {context.user_data}"
                print(error_message)  # Debug print
                await update.message.reply_text(f"⚠️ Hubo un error al generar tu carta astral. Detalles: {error_message}")
                return ConversationHandler.END
        except Exception as e:
            error_message = f"Exception occurred: {str(e)}\nUser data: {context.user_data}"
            print(error_message)  # Debug print
            logger.error(error_message)
            await update.message.reply_text(f"⚠️ Hubo un error al generar tu carta astral. Detalles: {error_message}")
            return ConversationHandler.END
    else:
        await update.message.reply_text("🌍 Ese código de país no parece válido. Por favor, introduce las dos letras que indican tu país (por ejemplo, ES para España, AR para Argentina).")
        return COUNTRY_CODE

async def repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    if response.lower().startswith('s'):
        await update.message.reply_text("🌠 ¡Maravilloso! ¿Cuál es el nombre de esta nueva alma?")
        return NAME
    else:
        await update.message.reply_text("✨ Lamentablemente, nuestros caminos se separan. ¡Espero que nuestros caminos se crucen de nuevo!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("✨ Lamentablemente, nuestros caminos se separan. ¡Espero que nuestros caminos se crucen de nuevo!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
         entry_points=[
            CommandHandler('start', start),  # Activates with the /start command
            MessageHandler(filters.TEXT & ~filters.COMMAND, start)  # Activates with any text
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year)],
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, month)],
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, day)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            COUNTRY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, country_code)],
            REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, repeat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
