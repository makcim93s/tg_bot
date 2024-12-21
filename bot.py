

import os
import csv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import logging
import re

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная таблица для хранения данных
table = []

# Состояние сессии
is_session_active = False

# Индекс текущего клиента
current_client = {}

# Столбцы таблицы
columns = [
    "Должность`", "Имя`", "Отчество`", "Мобильный телефон", "Адрес", 
    "Фото входной группы", "Тип автомата", 
    "Предложенная аренда (рубли)", "Описание, детали"
]

# Стартовое сообщение
async def start(update: Update, context: CallbackContext) -> None:
    # Создаем клавиатуру с кнопками "Начать сессию" и "Раздел помощи"
    keyboard = [
        [KeyboardButton("Начать сессию")],
        [KeyboardButton("Раздел помощи")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я бот для ввода данных. Выберите одну из опций:", 
        reply_markup=reply_markup
    )

# Начать сессию
async def handle_start_session(update: Update, context: CallbackContext) -> None:
    global is_session_active, current_client
    if not is_session_active:
        is_session_active = True
        current_client = {col: '' for col in columns}  # Сбрасываем данные клиента
        keyboard = [[KeyboardButton("Сбросить")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('Сессия начата, давайте начнем заполнять данные.', reply_markup=reply_markup)
        await ask_for_position(update, context)  # Спрашиваем Должность
    else:
        await update.message.reply_text('Сессия уже активна.')

# Раздел помощи
async def handle_help(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Этот бот предназначен для ввода данных о клиентах.\n\n"
        "1. Чтобы начать сессию, нажмите 'Начать сессию'.\n"
        "2. Бот попросит вас ввести данные по каждому клиенту: телефон,должность, имя, отчество, адрес, фото и другие параметры.\n"
        "3. После заполнения данных вы можете продолжить для следующего клиента или завершить сессию.\n"
        "4. Для завершения сессии нажмите кнопку 'Завершить'.\n"
        "5. По завершению, бот отправит CSV файл с введенными данными."
        "6. Для сброса нажмите в меню кнопку 'Сбросить'№."
    )
    await update.message.reply_text(help_text)

# Спрашиваем Должность
async def ask_for_position(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Введите должность.")
# Функция для проверки номера телефона
def is_valid_phone_number(phone: str) -> bool:
    phone_pattern = re.compile(r'^(?:\+?(\d{1,2}))?(\()?(\d{3})(?(2)\))(\d{3})(\d{2})(\d{2})$')
    return bool(phone_pattern.match(phone))
    #Функция для обработки фотографии
async def handle_photo(update: Update, context: CallbackContext) -> None:
    global current_client
    # Получаем ID фото и ссылку на него
    photo_id = update.message.photo[-1].file_id
    file = await context.bot.get_file(photo_id)
    photo_url = file.file_path  # Получаем прямую ссылку на фото

    # Добавляем ссылку на фото в таблицу
    current_client["Фото входной группы"] = photo_url

    # Отправляем сообщение пользователю, что фото загружено
    await update.message.reply_text(f"Фото загружено! Ссылка на фото добавлена в таблицу:\n{photo_url}")

    # Переходим к следующему запросу (например, тип автомата)
    await update.message.reply_text("Теперь введите тип автомата.")

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: CallbackContext) -> None:
    global current_client
    text = update.message.text

    # Проверяем, что сессия активна
    if is_session_active:
        # Если должность еще не введена
        if current_client["Должность"] == '':
            current_client["Должность"] = text
            await update.message.reply_text("Теперь введите имя и отчество (если есть).")
        # Если имя и отчество еще не введены
        elif current_client["Имя"] == '':
            name_parts = text.split(" ", 1)
            current_client["Имя"] = name_parts[0]
            if len(name_parts) > 1:
                current_client["Отчество"] = name_parts[1]
            else:
                current_client["Отчество"] = ''
            await update.message.reply_text("Теперь введите номер телефона")
        # Если номер телефона еще не введен
        elif current_client["Мобильный телефон"] == '':
            if is_valid_phone_number(text):
                current_client["Мобильный телефон"] = text
                await update.message.reply_text("Теперь введите адрес.")
            else:
                await update.message.reply_text("Ошибка! Неверный формат номера телефона. Введите номер в правильном формате (например,+7(999)9005050.")
            
        # Если адрес еще не введен
        elif current_client["Адрес"] == '':
            current_client["Адрес"] = text
            await update.message.reply_text("Теперь отправьте фото входной группы.")
        # Если фото входной группы еще не введено
        elif current_client["Фото входной группы"] == '':
            await update.message.reply_text("Пожалуйста, отправьте фото входной группы.")
            await update.message.reply_text("Теперь введите тип автомата.")
        # Если тип автомата еще не введен
        elif current_client["Тип автомата"] == '':
            current_client["Тип автомата"] = text
            await update.message.reply_text("Теперь введите предложенную аренду (в рублях).")
        # Если аренда еще не введена
        elif current_client["Предложенная аренда (рубли)"] == '':
            current_client["Предложенная аренда (рубли)"] = text
            await update.message.reply_text("Теперь введите описание и детали.")
        # Если описание еще не введено
        elif current_client["Описание, детали"] == '':
            current_client["Описание, детали"] = text
            await show_continue_finish_buttons(update, context)  # Показываем кнопки для продолжения или завершения
        else:
            await update.message.reply_text("Неизвестная ошибка.")

# Функция для вывода кнопок продолжения или завершения
async def show_continue_finish_buttons(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Продолжить", callback_data="continue")],
        [InlineKeyboardButton("Завершить", callback_data="finish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Данные для текущего клиента сохранены. Хотите продолжить для следующего клиента или завершить сессию?", reply_markup=reply_markup)

# Обработчик кнопок "Продолжить" и "Завершить"
async def handle_button(update: Update, context: CallbackContext) -> None:
    global is_session_active, current_client, table
    query = update.callback_query
    await query.answer()

    if query.data == "continue":
        # Сохраняем текущего клиента в таблицу перед сбросом
        table.append([current_client[col] for col in columns])

        # Если нажали "Продолжить", сбрасываем данные для нового клиента
        current_client = {col: '' for col in columns}
        await query.edit_message_text("Заполнение следующего клиента. Введите должность.")
        await ask_for_position(update, context)

    elif query.data == "finish":
        # Сохраняем данные текущего клиента в таблицу
        table.append([current_client[col] for col in columns])

        # Текущая рабочая директория
        logger.info(f"Текущая рабочая директория: {os.getcwd()}")

        # Сохраняем таблицу в CSV файл
        file_name = "data.csv"
        file_path = os.path.join(os.getcwd(), file_name)  # Путь к файлу

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Записываем заголовок таблицы
                writer.writerow(columns)
                # Записываем данные таблицы
                for row in table:
                    writer.writerow(row)
            logger.info(f"Файл {file_path} успешно сохранен.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {e}")
            await query.edit_message_text("Произошла ошибка при сохранении файла.")
            return

        # Отправляем CSV файл пользователю
        try:
            with open(file_path, 'rb') as file:
                await query.message.reply_document(document=file, filename=file_name)
            logger.info(f"Файл {file_name} успешно отправлен.")
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await query.edit_message_text("Произошла ошибка при отправке файла.")

        # Завершаем сессию
        is_session_active = False
        table.clear()  # Очищаем таблицу после отправки
        await query.edit_message_text("Сессия завершена и файл отправлен.")
    else:
        await query.edit_message_text("Нет активной сессии.")

# Обработчик кнопки "Закончить предварительно"
async def handle_end_session_early(update: Update, context: CallbackContext) -> None:
    global is_session_active, current_client, table
    # Сбросить состояние сессии
    is_session_active = False
    current_client = {}
    table.clear()  # Очищаем таблицу

    # Создаем клавиатуру для начала новой сессии
    keyboard = [
        [KeyboardButton("Начать сессию")],
        [KeyboardButton("Раздел помощи")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Информируем пользователя о завершении и предлагаем начать заново
    await update.message.reply_text(
        "Сессия завершена. Вы можете начать новую сессию или получить помощь.",
        reply_markup=reply_markup
    )

# Изменяем обработку кнопок в main
def main():
    # Токен твоего бота
    TOKEN = '7801966987:AAGXfCKmOZiOatUPWOJbEg4R8v39T0QqXYM'

    # Создаем объект Application
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))

    # Обработчик кнопок "Продолжить" и "Завершить"
    application.add_handler(CallbackQueryHandler(handle_button))
    
    # Обработчик кнопки "Закончить предварительно"
    application.add_handler(MessageHandler(filters.Regex('^Сбросить$'), handle_end_session_early))

    # Обработчики кнопок для начала сессии и помощи
    application.add_handler(MessageHandler(filters.Regex('^Начать сессию$'), handle_start_session))
    application.add_handler(MessageHandler(filters.Regex('^Раздел помощи$'), handle_help))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Обработчики фото
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
