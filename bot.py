import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.utils.executor import start_webhook
from config import TEXT, CHAT_ID


WEBHOOK_HOST = 'https://farm-hub-bot.herokuapp.com'  # name your app
WEBHOOK_PATH = '/webhook/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.environ.get('PORT')
TOKEN = os.environ['TOKEN']
logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()
bot = Bot(token=TOKEN, loop=loop, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

def_list = []
lm_id = 0


def get_def_msg():
    global def_list
    return '{}({})\n<b>{}</b>'.format(TEXT['ANS'], str(len(def_list)), ', '.join(def_list))


keyboard = types.InlineKeyboardMarkup()
keyboard.row_width = 2
keyboard.add(types.InlineKeyboardButton(text=TEXT['BTN_SWITCH'], callback_data='go'),
             types.InlineKeyboardButton(text=TEXT['BTN_DEF'], switch_inline_query='d'))


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(TEXT['START'])


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.reply(' '.join(TEXT['HELP']))


async def send_def(chat_id, msg_text, kb):
    result = await bot.send_message(chat_id=chat_id, text=msg_text, reply_markup=kb)
    global lm_id
    lm_id = result.message_id


# повторная отправка текущего статуса по команде с изменением глобальной переменной с ID последнего сообщения
@dp.message_handler(commands=['bot'])
async def send_def_message(message: types.Message):
    await send_def(CHAT_ID, get_def_msg(), keyboard)


# обновление списка защитников
def update_def_list(user_name: str):
    global def_list
    if user_name in def_list:
        def_list.remove(user_name)
    else:
        def_list.append(user_name)


# если запрос от последнего сообщения с data = 'go'
@dp.callback_query_handler(lambda c: c.message.message_id == lm_id and c.data == 'go')
async def process_callback_btn_go(callback_query: types.CallbackQuery):
    update_def_list(callback_query.from_user.username)
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(text=get_def_msg(),
                                chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                reply_markup=keyboard)


# ответ на все нажатия кнопок
@dp.callback_query_handler(lambda c: c.data != 'go')
async def process_all_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)


@dp.inline_handler(lambda query: query.query == 'd')
async def inline_def(inline_query: types.InlineQuery):
    input_content = types.InputTextMessageContent("/g_def HUB")
    item1 = types.InlineQueryResultArticle(id='1', title='🛡 HUB', input_message_content=input_content)
    try:
        await bot.answer_inline_query(inline_query.id, results=[item1], cache_time=1)
    except Exception as e:
        print(e)


# сброс списка защитников и отправка сообщения
async def reset_def_list():
    global def_list
    def_list = []
    await send_def(CHAT_ID, get_def_msg(), keyboard)


# запускаем отправку сообщения по расписанию
time_do_it = [(22, 10), (6, 10), (14, 10)]
scheduler = AsyncIOScheduler()
for h, m in time_do_it:
    scheduler.add_job(reset_def_list, 'cron', hour=h, minute=m)
scheduler.start()


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    # insert code here to run it before shutdown
    pass


if __name__ == '__main__':
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH,
                  on_startup=on_startup, on_shutdown=on_shutdown,
                  host=WEBAPP_HOST, port=WEBAPP_PORT)
