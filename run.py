#!/usr/bin/env python
import logging
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from kerykeion import Report, AstrologicalSubject
import requests, asyncio

# Enable logging to file
logging.basicConfig(filename='bot_activity.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for conversation stages
(NAME, YEAR, MONTH, DAY, TIME, LOCATION, RESULT, REPEAT) = range(8)

# API Keys
TELEGRAM_TOKEN = "7005636792:AAFsRSBKvxA67FoQao1f7AdjPxYKvwk9cvY"
OPENAI_API_KEY = "sk-proj-qB50VcbkJBZdzm5dXV9PT3BlbkFJBAK619TeTVNu76CPHaM8"

# Helper functions
def remove_leading_zeros(number_str):
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

def create_astro_chart(name, year, month, day, hour, minute, location):
    subject = AstrologicalSubject(name, int(year), int(month), int(day), int(hour), int(minute), location)
    report = Report(subject)
    full_report = report.get_full_report()
    return format_chart(full_report)

def format_chart(chart):
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
    endpoint = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    prompt = f"""
    🌟🔮 You are a witch skilled in reading people. Here is the astrological chart of someone special. Based on it, perform a cold reading about this person. Dive deep into key aspects such as hobbies, family, work, and love life. Remember, you are a clever and skilled little witch, capable of making very precise assertions with absolute certainty:

    {chart}

    🧙‍♀️ The person's name is {name}. Talk to {name} in the second person, as if you were speaking directly to them. Do not mention the astrological chart directly; use it only as a guide in your predictions. Imagine their hobbies and what they value most in life and day-to-day. Consider their possible age (GenZ or Millennial) and gender (determine from the name), as well as their origin from {location}. Use plenty of emojis in the response, one or two per paragraph, making them relevant to what you are saying. 🌌✨
    """
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'system', 'content': 'You are an expert witch at reading people through their astrological charts. Use your skill to reveal precise and deep details about their lives, interests, and personalities.'},
                     {'role': 'user', 'content': prompt}]
    }
    response = requests.post(endpoint, headers=headers, json=data)
    prediction_response = response.json()
    content = prediction_response['choices'][0]['message']['content']
    return content

def log_user_interaction(context):
    with open("users.txt", "a") as file:
        user_data = context.user_data
        file.write(f"Name: {user_data.get('name', 'Unknown')}\n")
        file.write(f"Date: {user_data.get('day', 'DD')}-{user_data.get('month', 'MM')}-{user_data.get('year', 'YYYY')}\n")
        file.write(f"Time: {user_data.get('hour', 'HH')}:{user_data.get('minute', 'MM')}\n")
        file.write(f"Location: {user_data.get('location', 'Unknown')}\n")
        file.write("-------------------------------\n")

# Handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🌙✨ Greetings! My name is Lunastar and I am here to explore the mysteries of your astrology. What's your name?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) > 40:
        await update.message.reply_text("🔮 Your name seems quite long, can you give me a shorter one?")
        return NAME
    context.user_data["name"] = name
    await update.message.reply_text("🌟 A pleasure to meet you, in which year (YYYY) did you first cross the threshold of time?")
    return YEAR

async def year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    year = remove_leading_zeros(update.message.text)
    if year is not None and 1900 <= int(year) <= 2027:
        context.user_data["year"] = year
        await update.message.reply_text("📅 Now tell me, in which month (MM) did the sun first see you born?")
        return MONTH
    else:
        await update.message.reply_text("⏳ That year doesn't seem valid, please try another.")
        return YEAR

async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    month = remove_leading_zeros(update.message.text)
    if month is not None and 1 <= int(month) <= 12:
        context.user_data["month"] = month
        await update.message.reply_text("🌒 Interesting, and on what day (DD) did you awaken to this world?")
        return DAY
    else:
        await update.message.reply_text("📆 That month doesn't seem valid, please try another.")
        return MONTH

async def day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    day = remove_leading_zeros(update.message.text)
    if day is not None and 1 <= int(day) <= 31:
        context.user_data["day"] = day
        await update.message.reply_text("⏰ At what time did your magic begin to flow? Tell me the hour in HH:MM format (24h)")
        return TIME
    else:
        await update.message.reply_text("🗓️ That day doesn't seem valid, please try another.")
        return DAY

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hour, minute = validate_time(update.message.text)
    if hour is not None:
        context.user_data["hour"] = hour
        context.user_data["minute"] = minute
        await update.message.reply_text("🌍 Fascinating, what is the place of power where your essence was first invoked? (Indicate the nearest major city)")
        return LOCATION
    else:
        await update.message.reply_text("⌛ Please make sure to use the correct format HH:MM.")
        return TIME

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.text.strip()
    if len(location) <= 50:
        context.user_data["location"] = location
        chart = create_astro_chart(context.user_data["name"], context.user_data["year"],
                                   context.user_data["month"], context.user_data["day"],
                                   context.user_data["hour"], context.user_data["minute"],
                                   context.user_data["location"])
        await update.message.reply_text(f"🌌 Here is your astrological chart, revealed before me!\n{chart}")
        await update.message.reply_text("🔮 Give me a moment while the little witch consults the stars and weaves your prediction...")
        prediction = get_astrological_prediction(context.user_data["name"], context.user_data["location"], chart)
        
        await update.message.reply_text("⭐ With the stars as my witness, here is your prediction:")
        await asyncio.sleep(2)  # 2-second pause for suspense

        prediction_paragraphs = prediction.split('\n')
        for paragraph in prediction_paragraphs:
            if paragraph.strip():  # Only send non-empty paragraphs
                await update.message.reply_text(paragraph)
                await asyncio.sleep(7)  # 7-second pause between paragraphs

        log_user_interaction(context)  # Log user interaction
        await asyncio.sleep(10)  # 10-second pause before asking if they want to continue
        await update.message.reply_text(
            '🌟 I hope my words resonate with you! Would you like to keep asking about other souls you wish to know more about?'
        )
        return REPEAT
    else:
        await update.message.reply_text("🌆 That place seems too long, can you indicate a nearer major city?")
        return LOCATION

async def ask_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Yes', 'No']]
    await update.message.reply_text(
        '🌟 I hope my words resonate with you! Would you like to keep asking about other souls you wish to know more about?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?')
    )
    return REPEAT

async def repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer.lower().startswith('y'):
        await update.message.reply_text("🌠 Wonderful! What is the name of this new soul?")
        return NAME
    else:
        await update.message.reply_text("✨ Unfortunately, we part ways. I hope our paths cross again!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('✨ Unfortunately, we part ways. I hope our paths cross again!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
         entry_points=[
            CommandHandler('start', start),  # Triggers on /start command
            MessageHandler(filters.TEXT & ~filters.COMMAND, start)  # Triggers on any text 
        ],
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
