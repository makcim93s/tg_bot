

import os
import csv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import logging
import re
import random




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
        "Привет! Я — бот, который поможет тебе собрать все данные о клиентах и организовать их в удобной таблице. \n\nТы можешь ввести информацию о клиенте, загрузить фотографии, выбрать тип автомата, указать аренду и многое другое! \n\nЯ готов помочь тебе с этим, а если что-то будет непонятно, всегда можешь обратиться в раздел помощи! \n\nДавай начнем сессию и внесем все данные, как настоящий профессионал! ", 
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
        "3. После заполнения данных вы можете заполнять следующего клиента или завершить сессию.\n"
        "4. Для завершения сессии нажмите кнопку 'Завершить'.\n"
        "5. По завершению, бот отправит CSV файл с введенными данными."
        "6. Для сброса нажмите в меню кнопку 'Сбросить' - это сбросит полностью все данные без сохранения!!!"
        "\n\n\nСоздатель бота — @makcim93s. "
    )
    await update.message.reply_text(help_text)

# Спрашиваем Должность
async def ask_for_position(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Введите должность.")
    #Функция проверки номера
def is_valid_phone_number(phone: str) -> bool:
    # Убираем все пробелы и дефисы из номера телефона
    phone = phone.replace(" ", "").replace("-", "")
    
    # Проверяем, что номер состоит из 11 цифр, возможно с кодом страны
    return bool(re.match(r'^\+?(\d{1,2})?(\d{3})\d{3}\d{2}\d{2}$', phone))

# Функция для обработки типа автомата
async def ask_for_machine_type(update: Update, context: CallbackContext) -> None:
    keyboard = [
    [InlineKeyboardButton("Street (маленький)", callback_data="type_Street")],
    [InlineKeyboardButton("Slim (улица высокий)", callback_data="type_Slim")],
    [InlineKeyboardButton("Barrel (самый большой)", callback_data="type_Barrel")],
    [InlineKeyboardButton("House (помещение)", callback_data="type_House")],
    [InlineKeyboardButton("Mini-street (самый маленький)", callback_data="type_Mini-street")]
    ]   
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Пожалуйста, выберите тип автомата:", reply_markup=reply_markup)
    

# Обработчик кнопок выбора типа автомата
async def handle_machine_type(update: Update, context: CallbackContext) -> None:
    global current_client
    query = update.callback_query
    await query.answer()

    # Сопоставление callback_data с названиями
    machine_type_mapping = {
        "type_Street": "Street",
        "type_Slim": "Slim",
        "type_Barrel": "Barrel",
        "type_House": "House",
        "type_Mini-street": "Mini-street"
    }

    # Получаем название типа автомата
    selected_type = machine_type_mapping.get(query.data, None)
    if selected_type:
        # Записываем в таблицу
        current_client["Тип автомата"] = selected_type
        await query.edit_message_text(f"Тип автомата выбран: {selected_type}. \n\nТеперь введите предложенную аренду (в рублях).")
    else:
        await query.edit_message_text("Неверный выбор типа автомата.")






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
    await update.message.reply_text(f"Фото загружено! Ссылка на фото добавлена в таблицу.")

    # Немедленно предлагаем выбрать тип автомата
    await ask_for_machine_type(update, context)
    
    
    
    
    


# Обработчик текстовых сообщений
async def handle_text(update: Update, context: CallbackContext) -> None:
    global current_client
    text = update.message.text

    # Проверяем, что сессия активна
    if is_session_active:
        # Если должность еще не введена
        if current_client["Должность`"] == '':
            current_client["Должность`"] = text
            await update.message.reply_text("Теперь введите имя и отчество (если есть).")
        # Если имя и отчество еще не введены
        elif current_client["Имя`"] == '':
            name_parts = text.split(" ", 1)
            current_client["Имя`"] = name_parts[0]
            if len(name_parts) > 1:
                current_client["Отчество`"] = name_parts[1]
            else:
                current_client["Отчество`"] = ''
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
        # Если тип автомата еще не введен
        elif current_client["Тип автомата"] == '':
            await ask_for_machine_type(update, context) # Переход к запросу типа автомата
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

import random

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

        # Отправляем случайное изображение
        images_dir = r"C:\users\administrator\downloads\bots\photo" # Название директории с фотографиями
        try:
            if os.path.exists(images_dir) and os.path.isdir(images_dir):
                images = [os.path.join(images_dir, f) for f in os.listdir(images_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
                if images:
                    random_image = random.choice(images)
                    with open(random_image, 'rb') as img_file:
                        await query.message.reply_photo(photo=img_file)
                    logger.info(f"Случайное изображение {random_image} отправлено.")
                else:
                    logger.warning("Директория с изображениями пуста.")
                    await query.message.reply_text("Не удалось отправить изображение: директория пуста.")
            else:
                logger.warning("Директория с изображениями не найдена.")
                await query.message.reply_text("Не удалось отправить изображение: директория не найдена.")
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            await query.message.reply_text("Произошла ошибка при отправке изображения.")

        # Завершаем сессию
        is_session_active = False
        table.clear()  # Очищаем таблицу после отправки
        await query.edit_message_text("Сессия завершена и файл отправлен. Ты молодец получи бонус за хорошую работу!")
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
    
    # Обработчик кнопок выбора типа автомата
    application.add_handler(CallbackQueryHandler(handle_machine_type, pattern="^type_"))



    

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
