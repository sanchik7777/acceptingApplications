import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import ChatJoinRequest
import logging
from background import keep_alive

BOT_TOKEN = '7551027634:AAENbSzLtmERfDRoBccUb0vsuMehvLVjP6g'
CHANNEL_ID = -1002184700377
ADMIN_ID = 7002244661

# Очередь для обработки заявок
queue = asyncio.Queue()

# Семафор для ограничения числа параллельных заявок
semaphore = asyncio.Semaphore(5)  # Максимум 5 заявок одновременно

async def approve_request_worker(bot: Bot):
    """
    Воркер для обработки заявок из очереди.
    """
    while True:
        chat_join = await queue.get()
        async with semaphore:  # Ограничиваем количество параллельных обработок
            try:
                msg = (
                    "<b>Заявка подана успешно!</b>\n\n"
                    "Мы предлагаем уникальную возможность зарабатывать на TikTok. "
                    "Уделяй от 2 до 6 часов в неделю, создавая контент на интересную тебе тему. "
                    "Прибыль 50 на 50. Мы не продаем курсы, а работаем напрямую с партнерами.\n\n"
                    "Все вопросы — @tiktok_partners. Не стесняйся, пиши – мы не кусаемся 😄."
                )

                image_url = "https://cdn.discordapp.com/attachments/1224751404711673879/1316872219015774319/Group_4.jpg?ex=675ca053&is=675b4ed3&hm=abf16e15afe9a404e485476b865cc00f60f64ab114d9d1e5ca7338c79a9fd2b3&"

                # Отправка фото и одобрение заявки
                await bot.send_photo(
                    chat_id=chat_join.from_user.id,
                    photo=image_url,
                    caption=msg,
                    parse_mode="HTML",
                )
               
                logging.info(f"Заявка от {chat_join.from_user.id} отправлена")
            except Exception as e:
                logging.error(f"Ошибка при обработке заявки: {e}")
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Ошибка при обработке заявки от {chat_join.from_user.id}: {e}",
                )
            finally:
                queue.task_done()  # Уведомляем очередь об обработке

async def handle_new_join_request(chat_join: ChatJoinRequest, bot: Bot):
    """
    Добавление новой заявки в очередь.
    """
    await queue.put(chat_join)
    logging.info(f"Заявка от {chat_join.from_user.id} добавлена в очередь")

async def start():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация обработчика заявок
    dp.chat_join_request.register(handle_new_join_request, F.chat.id == CHANNEL_ID)

    # Запуск воркера для обработки заявок
    asyncio.create_task(approve_request_worker(bot))

    try:
        logging.info("Бот запущен и начал polling...")
        await dp.start_polling(bot)
    except Exception as ex:
        logging.error(f"Ошибка: {ex}")
    finally:
        await bot.session.close()
keep_alive()
if __name__ == "__main__":
    asyncio.run(start())
