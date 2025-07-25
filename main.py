import asyncio
import random
from aiogram import types, Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from typing import Dict, List

COMMAND_WEATHER = "weather"
COMMAND_CONVERT = "convert"
COMMAND_HELP = "help"
BUTTON_UPDATE = "Обновить данные"

CELSIUS = "℃ (Цельсий)"
FAHRENHEIT = "℉ (Фаренгейт)"
ACCESS_CITIES = ("moscow", "volgograd", "saratov")

bot = Bot(token='')
dp = Dispatcher()

database: Dict[int, str] = {}
session_log: List[str] = []
current_temp: int = None
current_temp_type: str = None
current_city: str = None

def keyboard_builder(buttons_list: list, keyboard_size: int) -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    for button in buttons_list:
        builder.add(types.KeyboardButton(text=str(button)))

    builder.adjust(keyboard_size)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_weather(city_name: str) -> str:
    global current_city, current_temp, current_temp_type

    if not city_name:
        return ("Чтобы узнать погоду, введите название города после команды /weather\n"
                "Например: /weather Moscow\n"
                "Доступные города: Moscow, Volgograd, Saratov")

    city_name = city_name.lower()
    if city_name not in ACCESS_CITIES:
        return ("К сожалению, я не могу показать погоду для этого города.\n"
                "Доступные города:\n"
                "- Moscow\n"
                "- Volgograd\n"
                "- Saratov\n"
                "Попробуйте один из них!")

    temperature_range = (-10, 30) if current_temp_type == CELSIUS else (14, 86)
    current_temp = random.randint(*temperature_range)
    current_city = city_name

    session_log.append("take_weather_city")

    return (f"Погода в городе {city_name.capitalize()}:\n"
            f"Температура: {current_temp} {current_temp_type}\n"
            f"Состояние: ясно\n"
            f"Можете обновить данные кнопкой ниже или конвертировать температуру командой /convert")

@dp.message(Command("start"))
async def start_dialogue(message: types.Message):
    session_log.append("/start")
    user_id = message.from_user.id

    if user_id not in database:
        database[user_id] = CELSIUS

    keyboard = keyboard_builder([CELSIUS, FAHRENHEIT], 2)
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        "Я - бот для отслеживания погоды и конвертации температур.\n\n"
        "Пожалуйста, выберите предпочитаемую шкалу температуры:",
        reply_markup=keyboard
    )

@dp.message(F.text.in_([CELSIUS, FAHRENHEIT]))
async def temp_type_choice(message: types.Message):
    global current_temp_type

    if not session_log or session_log[-1] != "/start":
        return

    session_log.append("temp_type_choice")
    user_id = message.from_user.id
    chosen_type = message.text

    database[user_id] = chosen_type
    current_temp_type = chosen_type

    await message.reply(
        f"Отлично! Вы выбрали {chosen_type}.\n\n"
        "Теперь вы можете:\n"
        "- Узнать погоду: /weather <город>\n"
        "- Посмотреть список команд: /help\n\n"
        "Начните с запроса погоды для одного из доступных городов!"
    )

@dp.message(Command(COMMAND_HELP))
async def help_command(message: types.Message):
    help_text = (
        "Доступные команды:\n\n"
        "/start - Начать работу с ботом заново\n"
        "/weather <город> - Узнать текущую погоду в выбранном городе\n"
        "/convert - Конвертировать текущую температуру между шкалами\n\n"
        "Доступные города: Moscow, Volgograd, Saratov\n\n"
        "Для начала просто запросите погоду в нужном городе!"
    )
    await message.answer(help_text)

@dp.message(Command(COMMAND_WEATHER))
async def take_weather_city(message: types.Message, command: CommandObject):
    global current_city

    city = command.args
    weather_response = get_weather(city)

    keyboard = keyboard_builder([BUTTON_UPDATE], 1) if city and city.lower() in ACCESS_CITIES else None

    await message.answer(weather_response, reply_markup=keyboard)

@dp.message(F.text == BUTTON_UPDATE)
async def weather_update(message: types.Message):
    if not current_city:
        await message.answer("Сначала запросите погоду для города с помощью /weather <город>")
        return

    await message.answer("Обновляю данные о погоде...")
    await message.answer(get_weather(current_city))

@dp.message(Command(COMMAND_CONVERT))
async def temp_convert(message: types.Message):
    if not current_temp or not current_temp_type:
        await message.answer(
            "Сначала запросите погоду для города с помощью /weather <город>, "
            "а затем я смогу конвертировать температуру!"
        )
        return

    if current_temp_type == CELSIUS:
        converted_temp = int(current_temp * 9 / 5 + 32)
        new_type = FAHRENHEIT
        conversion_msg = "Цельсий → Фаренгейт"
    else:
        converted_temp = int((current_temp - 32) * 5 / 9)
        new_type = CELSIUS
        conversion_msg = "Фаренгейт → Цельсий"

    session_log.append("temp_convert")
    await message.answer(
        f"Результат конвертации ({conversion_msg}):\n\n"
        f"Температура в {current_city.capitalize()}:\n"
        f"Было: {current_temp} {current_temp_type}\n"
        f"Стало: {converted_temp} {new_type}\n\n"
        f"Можете снова запросить погоду или обновить текущие данные!"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())