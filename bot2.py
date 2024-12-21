from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Отправьте изображение, и я дам вам прямую ссылку на него.")

def handle_photo(update: Update, context: CallbackContext) -> None:
    # Получаем файл изображения
    photo = update.message.photo[-1]
    # Получаем ID файла
    file_id = photo.file_id
    # Получаем URL для скачивания
    file = context.bot.get_file(file_id)
    file_url = file.file_path
    
    # Отправляем пользователю прямую ссылку на изображение
    update.message.reply_text(f"Вот ссылка на ваше изображение: {file_url}")

def main() -> None:
    # Токен вашего бота
    token = '7801966987:AAGXfCKmOZiOatUPWOJbEg4R8v39T0QqXYM'
    
    updater = Updater(token)
    dispatcher = updater.dispatcher
    
    # Обработчики команд и сообщений
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
