import contextlib
import asyncio
from aiogram.types import ChatJoinRequest
from aiogram import Bot, Dispatcher, F
import logging
from background import keep_alive

BOT_TOKEN = '7551027634:AAENbSzLtmERfDRoBccUb0vsuMehvLVjP6g'
CHANNEL_ID = -1002184700377
ADMIN_ID = 7002244661
BATCH_SIZE = 5  # Количество заявок, обрабатываемых одновременно
DELAY_BETWEEN_BATCHES = 1  # Задержка между партиями в секундах

async def process_batch(batch, bot):
    """
    Обрабатывает партию заявок.
    :param batch: Список объектов ChatJoinRequest
    :param bot: Экземпляр бота
    """
    tasks = []
    for chat_join in batch:
        tasks.append(approve_request(chat_join, bot))
    
    # Параллельно обрабатываем заявки
    await asyncio.gather(*tasks)

async def approve_request(chat_join: ChatJoinRequest, bot: Bot):
    """
    Обработка заявки на вступление в канал. Отправляет сообщение с изображением
    из URL и одобряет заявку.
    """
    msg = (
        f"<b>Заявка подана успешно!</b>\n\n"
        f"Мы предлагаем уникальную возможность зарабатывать на TikTok. Уделяй от 2 до 6 часов в неделю, создавая контент на интересную тебе тему. Прибыль 50 на 50. Мы не продаем курсы, а работаем напрямую с партнерами.\n\n"
        f"Все вопросы — @tiktok_partners. Не стесняйся, пиши – мы не кусаемся 😄."
    )

    # Ссылка на изображение
    image_url = "https://cdn.discordapp.com/attachments/1224751404711673879/1316872219015774319/Group_4.jpg"

    try:
        # Отправка фото с сообщением
        await bot.send_photo(
            chat_id=chat_join.from_user.id,
            photo=image_url,
            caption=msg,
            parse_mode="HTML"
        )

        # Одобрение заявки
        await chat_join.approve()
        logging.info(f"Заявка от {chat_join.from_user.id} одобрена")
    except Exception as e:
        logging.error(f"Ошибка при обработке заявки: {e}", exc_info=True)
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Ошибка при обработке заявки от {chat_join.from_user.id}: {e}"
        )

async def start():
    """Запуск бота и настройка диспетчера."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Очередь заявок
    pending_requests = []

    # Обработчик заявок
    @dp.chat_join_request.register(F.chat.id == CHANNEL_ID)
    async def handle_request(chat_join: ChatJoinRequest):
        nonlocal pending_requests
        pending_requests.append(chat_join)

    async def process_requests():
        nonlocal pending_requests
        while True:
            if pending_requests:
                batch = pending_requests[:BATCH_SIZE]
                pending_requests = pending_requests[BATCH_SIZE:]

                await process_batch(batch, bot)
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)
            else:
                await asyncio.sleep(0.5)

    try:
        logging.info("Бот запущен и начал polling...")
        asyncio.create_task(process_requests())  # Запуск обработки заявок
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as ex:
        logging.error(f"[Exception] - {ex}", exc_info=True)
    finally:
        await bot.session.close()

keep_alive()
if __name__ == '__main__':
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(start())
