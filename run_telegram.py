#!/usr/bin/env python
import logging
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from kerykeion import Report, AstrologicalSubject
import requests

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stages
(NAME, YEAR, MONTH, DAY, TIME, LOCATION, RESULT, REPEAT) = range(8)

# Helper function to remove leading zeros and validate numeric input
def remove_leading_zeros(number_str):
    try:
        return str(int(number_str))
    except ValueError:
        return None

# Function to validate time input
def validate_time(time_str):
    try:
        hour, minute = map(int, time_str.split(":"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
        else:
            return None, None
    except ValueError:
        return None, None

# Function to create an astrological chart
def create_astro_chart(name, year, month, day, hour, minute, location):
    subject = AstrologicalSubject(name, int(year), int(month), int(day), int(hour), int(minute), location)
    report = Report(subject)
    full_report = report.get_full_report()
    return format_chart(full_report)

def format_chart(chart):
    part_of_interest = "----------------------------------------\n" + chart.split("Date")[1]  # This assumes there is only one "Date" in the text
    lines = part_of_interest.split('\n')
    formatted_lines = []
    for line in lines:
        line = line.replace('+', '-')
        if '-' in line:
            line = line[:60]  # Limit line length after replacement
        formatted_lines.append(line)
    return "Date" + '\n'.join(formatted_lines)

# Function to call the OpenAI API with the astrological chart
def get_astrological_prediction(name, location, chart):
    api_key = 'sk-proj-qB50VcbkJBZdzm5dXV9PT3BlbkFJBAK619TeTVNu76CPHaM8'
    endpoint = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    prompt = f"""
    Eres una bruja experta en la lectura de cartas astrales. Analiza este perfil y diviértete un poco con las predicciones:

    {chart}

    La persona se llama {name}, y como buena bruja sabrás dirigirte correctamente. Basándote en su carta, adivina sus aficiones y lo que más valora en la vida y en el día a día. Vive en {location}.
    """
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'system', 'content': 'Eres una bruja muy habilidosa que se destaca en la lectura de personas basándote en sus cartas astrales. Realiza una lectura astuta.'},
                     {'role': 'user', 'content': prompt}]
    }
    response = requests.post(endpoint, headers=headers, json=data)
    prediction_response = response.json()
    content = prediction_response['choices'][0]['message']['content']
    return content

# Handler functions for the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "¡Saludos! Mi nombre es Miralunas y estoy aquí para explorar los misterios de tu astrología. ¿Cómo te llamas?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) > 40:
        await update.message.reply_text("Tu nombre parece muy largo, ¿puedes darme un nombre más corto?")
        return NAME
    context.user_data["name"] = name
    await update.message.reply_text("Un placer conocerte, ¿en qué año (AAAA) cruzaste por primera vez el umbral del tiempo?")
    return YEAR

async def year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    year = remove_leading_zeros(update.message.text)
    if year is not None and 1900 <= int(year) <= 2027:
        context.user_data["year"] = year
        await update.message.reply_text("Ahora dime, ¿en qué mes (MM) el sol te vio nacer?")
        return MONTH
    else:
        await update.message.reply_text("Ese año no parece válido, intenta otro por favor.")
        return YEAR

async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    month = remove_leading_zeros(update.message.text)
    if month is not None and 1 <= int(month) <= 12:
        context.user_data["month"] = month
        await update.message.reply_text("Interesante, ¿y qué día (DD) despertaste a este mundo?")
        return DAY
    else:
        await update.message.reply_text("Ese mes no parece válido, intenta otro por favor.")
        return MONTH

async def day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    day = remove_leading_zeros(update.message.text)
    if day is not None and 1 <= int(day) <= 31:
        context.user_data["day"] = day
        await update.message.reply_text("A la luz de qué momento tu magia comenzó a fluir? Dime la hora en formato HH:MM (24h)")
        return TIME
    else:
        await update.message.reply_text("Ese día no parece válido, intenta otro por favor.")
        return DAY

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hour, minute = validate_time(update.message.text)
    if hour is not None:
        context.user_data["hour"] = hour
        context.user_data["minute"] = minute
        await update.message.reply_text("Fascinante, ¿cuál es el lugar de poder donde tu esencia fue invocada por primera vez? (Indica la ciudad grande más cercana)")
        return LOCATION
    else:
        await update.message.reply_text("Por favor, asegúrate de usar el formato correcto HH:MM.")
        return TIME

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.text.strip()
    if len(location) <= 50:
        context.user_data["location"] = location
        chart = create_astro_chart(context.user_data["name"], context.user_data["year"],
                                   context.user_data["month"], context.user_data["day"],
                                   context.user_data["hour"], context.user_data["minute"],
                                   context.user_data["location"])
        await update.message.reply_text(f"¡Aquí está tu carta astral, revelada ante mí!\n{chart}")
        await update.message.reply_text("Permíteme unos instantes mientras la brujilla consulta los astros y teje tu predicción...")
        prediction = get_astrological_prediction(context.user_data["name"], context.user_data["location"], chart)
        await update.message.reply_text(f"Con las estrellas como testigo, aquí está tu predicción:\n{prediction}")
        return await ask_repeat(update, context)  # Use `await` to properly handle the coroutine
    else:
        await update.message.reply_text("Ese lugar parece muy largo, ¿puedes indicar una ciudad grande más cercana?")
        return LOCATION

async def ask_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Sí', 'No']]
    await update.message.reply_text(
        'Espero que mis palabras resuenen contigo! ¿Quieres seguir preguntándome por otras almas de las que desees conocer más?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder='Sí o No?')
    )
    return REPEAT

async def repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer.lower() == 'sí':
        await update.message.reply_text("¡Maravilloso! ¿Cómo se llama esta nueva alma?")
        return NAME
    else:
        await update.message.reply_text("Lamentablemente nos despedimos. ¡Espero que nuestros caminos se crucen de nuevo!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Lamentablemente nos despedimos. ¡Espero que nuestros caminos se crucen de nuevo!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token("7005636792:AAFsRSBKvxA67FoQao1f7AdjPxYKvwk9cvY").build()
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year)],
            MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, month)],
            DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, day)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, repeat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
