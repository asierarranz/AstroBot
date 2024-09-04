#!/usr/bin/env python
import os
from dotenv import load_dotenv
import logging
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from kerykeion import Report, AstrologicalSubject, KerykeionChartSVG
import requests, asyncio, unicodedata, time
import cairosvg

# Load environment variables
load_dotenv()

# Enable logging to a file
logging.basicConfig(filename='bot_activity.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for conversation stages
(NAME, YEAR, MONTH, DAY, TIME, LOCATION, COUNTRY_CODE, RESULT, REPEAT) = range(9)

# API keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

def replace_css_variables(svg_content):
    css_variables = {
        '--kerykeion-color-black': '#000000',
        '--kerykeion-color-white': '#ffffff',
        '--kerykeion-color-neutral-content': '#c8cbd0',
        '--kerykeion-color-base-content': '#ccd0d4',
        '--kerykeion-color-primary': '#38bdf8',
        '--kerykeion-color-secondary': '#818cf8',
        '--kerykeion-color-accent': '#f471b5',
        '--kerykeion-color-neutral': '#1e293b',
        '--kerykeion-color-base-100': '#0f172a',
        '--kerykeion-color-info': '#0ca5e9',
        '--kerykeion-color-info-content': '#000000',
        '--kerykeion-color-success': '#2dd4bf',
        '--kerykeion-color-warning': '#f4bf50',
        '--kerykeion-color-error': '#fb7085',
        '--kerykeion-color-base-200': '#0a1020',
        '--kerykeion-color-base-300': '#171f2c',
        '--kerykeion-chart-color-paper-0': '#c8cbd0',
        '--kerykeion-chart-color-paper-1': '#0f172a',
        '--kerykeion-chart-color-zodiac-bg-0': '#0a1020',
        '--kerykeion-chart-color-zodiac-bg-1': '#171f2c',
        '--kerykeion-chart-color-zodiac-bg-2': '#0a1020',
        '--kerykeion-chart-color-zodiac-bg-3': '#171f2c',
        '--kerykeion-chart-color-zodiac-bg-4': '#0a1020',
        '--kerykeion-chart-color-zodiac-bg-5': '#171f2c',
        '--kerykeion-chart-color-zodiac-bg-6': '#0a1020',
        '--kerykeion-chart-color-zodiac-bg-7': '#171f2c',
        '--kerykeion-chart-color-zodiac-bg-8': '#0a1020',
        '--kerykeion-chart-color-zodiac-bg-9': '#171f2c',
        '--kerykeion-chart-color-zodiac-bg-10': '#0a1020',
        '--kerykeion-chart-color-zodiac-bg-11': '#171f2c',
        '--kerykeion-chart-color-zodiac-radix-ring-0': '#1e293b',
        '--kerykeion-chart-color-zodiac-radix-ring-1': '#1e293b',
        '--kerykeion-chart-color-zodiac-radix-ring-2': '#1e293b',
        '--kerykeion-chart-color-zodiac-transit-ring-0': '#1e293b',
        '--kerykeion-chart-color-zodiac-transit-ring-1': '#1e293b',
        '--kerykeion-chart-color-zodiac-transit-ring-2': '#1e293b',
        '--kerykeion-chart-color-zodiac-transit-ring-3': '#1e293b',
        '--kerykeion-chart-color-houses-radix-line': '#ccd0d4',
        '--kerykeion-chart-color-houses-transit-line': '#ccd0d4',
        '--kerykeion-chart-color-conjunction': '#2dd4bf',
        '--kerykeion-chart-color-semi-sextile': '#2dd4bf',
        '--kerykeion-chart-color-semi-square': '#fb7085',
        '--kerykeion-chart-color-sextile': '#2dd4bf',
        '--kerykeion-chart-color-quintile': '#818cf8',
        '--kerykeion-chart-color-square': '#fb7085',
        '--kerykeion-chart-color-trine': '#2dd4bf',
        '--kerykeion-chart-color-sesquiquadrate': '#fb7085',
        '--kerykeion-chart-color-biquintile': '#818cf8',
        '--kerykeion-chart-color-quincunx': '#818cf8',
        '--kerykeion-chart-color-opposition': '#fb7085',
        '--kerykeion-chart-color-sun': '#f4bf50',
        '--kerykeion-chart-color-moon': '#818cf8',
        '--kerykeion-chart-color-mercury': '#38bdf8',
        '--kerykeion-chart-color-venus': '#f471b5',
        '--kerykeion-chart-color-mars': '#f4bf50',
        '--kerykeion-chart-color-jupiter': '#38bdf8',
        '--kerykeion-chart-color-saturn': '#818cf8',
        '--kerykeion-chart-color-uranus': '#f471b5',
        '--kerykeion-chart-color-neptune': '#38bdf8',
        '--kerykeion-chart-color-pluto': '#818cf8',
        '--kerykeion-chart-color-mean-node': '#f4bf50',
        '--kerykeion-chart-color-true-node': '#f4bf50',
        '--kerykeion-chart-color-chiron': '#818cf8',
        '--kerykeion-chart-color-first-house': '#f4bf50',
        '--kerykeion-chart-color-tenth-house': '#f4bf50',
        '--kerykeion-chart-color-seventh-house': '#f4bf50',
        '--kerykeion-chart-color-fourth-house': '#f4bf50',
        '--kerykeion-chart-color-mean-lilith': '#818cf8',
        '--kerykeion-chart-color-zodiac-icon-0': '#f471b5',
        '--kerykeion-chart-color-zodiac-icon-1': '#f4bf50',
        '--kerykeion-chart-color-zodiac-icon-2': '#38bdf8',
        '--kerykeion-chart-color-zodiac-icon-3': '#818cf8',
        '--kerykeion-chart-color-zodiac-icon-4': '#f471b5',
        '--kerykeion-chart-color-zodiac-icon-5': '#f4bf50',
        '--kerykeion-chart-color-zodiac-icon-6': '#38bdf8',
        '--kerykeion-chart-color-zodiac-icon-7': '#818cf8',
        '--kerykeion-chart-color-zodiac-icon-8': '#f471b5',
        '--kerykeion-chart-color-zodiac-icon-9': '#f4bf50',
        '--kerykeion-chart-color-zodiac-icon-10': '#38bdf8',
        '--kerykeion-chart-color-zodiac-icon-11': '#818cf8',
        '--kerykeion-chart-color-air-percentage': '#38bdf8',
        '--kerykeion-chart-color-earth-percentage': '#f4bf50',
        '--kerykeion-chart-color-fire-percentage': '#f471b5',
        '--kerykeion-chart-color-water-percentage': '#818cf8',
        '--kerykeion-chart-color-lunar-phase-0': '#000000',
        '--kerykeion-chart-color-lunar-phase-1': '#ffffff',
        '--kerykeion-chart-color-house-number': '#ccd0d4'
    }

    for var, value in css_variables.items():
        svg_content = svg_content.replace(f"var({var})", value)
    
    return svg_content

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
                    png_path = svg_path.replace('.svg', '.png')
                    
                    # Read SVG content and replace CSS variables
                    with open(svg_path, 'r') as svg_file:
                        svg_content = svg_file.read()
                    svg_content = replace_css_variables(svg_content)
                    with open(svg_path, 'w') as svg_file:
                        svg_file.write(svg_content)
                    
                    # Try to send SVG file
                    """
                    try:
                        with open(svg_path, 'rb') as svg_file:
                            await update.message.reply_document(InputFile(svg_file))
                    except Exception as e:
                        logger.error(f"Error sending SVG file: {e}")
                        await update.message.reply_text("⚠️ Hubo un problema al enviar tu carta astral en formato SVG.")
                    """
                    
                    # Try to convert and send PNG file
                    try:
                        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=4.0)  # Increase resolution by 4 times
                        with open(png_path, 'rb') as png_file:
                            await update.message.reply_document(InputFile(png_file))
                    except Exception as e:
                        logger.error(f"Error converting or sending PNG file: {e}")
                        await update.message.reply_text("⚠️ Hubo un problema al convertir o enviar tu carta astral en formato PNG.")
                    
                    # Remove both SVG and PNG files
                    try:
                        os.remove(svg_path)
                        os.remove(png_path)
                    except Exception as e:
                        logger.error(f"Error removing files: {e}")
                
                await update.message.reply_text("🔮 Dame un momento mientras consulto las estrellas y tejo tu predicción...")
                prediction = get_astrological_prediction(context.user_data["name"], context.user_data["location"], chart)
                
                await update.message.reply_text("⭐ Con las estrellas como testigo, aquí está tu predicción:")
                await asyncio.sleep(2)  # 2-second pause for suspense

                prediction_paragraphs = prediction.split('\n')
                for paragraph in prediction_paragraphs:
                    if paragraph.strip():  # Only send non-empty paragraphs
                        await update.message.reply_text(paragraph)
                        await asyncio.sleep(5)  # 5-second pause between paragraphs

                log_user_interaction(context)  # Log the user interaction
                await asyncio.sleep(8)  # 8-second pause before asking if they want to continue
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
                    png_path = svg_path.replace('.svg', '.png')
                    
                    # Read SVG content and replace CSS variables
                    with open(svg_path, 'r') as svg_file:
                        svg_content = svg_file.read()
                    svg_content = replace_css_variables(svg_content)
                    with open(svg_path, 'w') as svg_file:
                        svg_file.write(svg_content)
                    
                    # Try to send SVG file
                    """
                    try:
                        with open(svg_path, 'rb') as svg_file:
                            await update.message.reply_document(InputFile(svg_file))
                    except Exception as e:
                        logger.error(f"Error sending SVG file: {e}")
                        await update.message.reply_text("⚠️ Hubo un problema al enviar tu carta astral en formato SVG.")
                    """
                    
                    try:
                        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=4.0)  # Increase resolution by 4 times
                        with open(png_path, 'rb') as png_file:
                            await update.message.reply_document(InputFile(png_file))
                    except Exception as e:
                        logger.error(f"Error converting or sending PNG file: {e}")
                        await update.message.reply_text("⚠️ Hubo un problema al convertir o enviar tu carta astral en formato PNG.")
                    
                    # Remove both SVG and PNG files
                    try:
                        os.remove(svg_path)
                        os.remove(png_path)
                    except Exception as e:
                        logger.error(f"Error removing files: {e}")
                
                await update.message.reply_text("🔮 Dame un momento mientras consulto las estrellas y tejo tu predicción...")
                prediction = get_astrological_prediction(context.user_data["name"], context.user_data["location"], chart)
                
                await update.message.reply_text("⭐ Con las estrellas como testigo, aquí está tu predicción:")
                await asyncio.sleep(2)  # 2-second pause for suspense

                prediction_paragraphs = prediction.split('\n')
                for paragraph in prediction_paragraphs:
                    if paragraph.strip():  # Only send non-empty paragraphs
                        await update.message.reply_text(paragraph)
                        await asyncio.sleep(5)  # 5-second pause between paragraphs

                log_user_interaction(context)  # Log the user interaction
                await asyncio.sleep(8)  # 8-second pause before asking if they want to continue
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