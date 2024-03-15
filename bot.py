from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, InputFile
from aiogram.utils.deep_linking import get_start_link, decode_payload
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
import os
from db import *
import aioschedule
import asyncio
import requests
import json
from datetime import datetime, timedelta
from threading import Thread, Lock


user_temp={}

# Настройки бота
TOKEN = ''
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.DEBUG)
lock = Lock()

async def send_start_msg(callback_query):
    markup = types.InlineKeyboardMarkup(row_width=1)
    user = get_user_data(callback_query.from_user.id)
    if(user['subscription_type'] == 'free'):
        markup.add(types.InlineKeyboardButton(text="🔓 Get access!", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/start.html')))
    elif(user['subscription_type'] == 'no paid'):
        markup.add(types.InlineKeyboardButton(text="👛 Buy paid access now!", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/subscribtion.html')))
    else:
        markup.add(types.InlineKeyboardButton(text="👁 View jobs", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/jobs.html')))
        if(user['subscription_type'] == 'trial'):
            markup.add(types.InlineKeyboardButton(text="👛 Buy paid access now!", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/subscribtion.html')))

    markup.add(types.InlineKeyboardButton(text="👋🏻 Referral program", callback_data="reflink"))
    markup.add(types.InlineKeyboardButton(text="⚙️ Settings", callback_data="job_settings"))
    count = count_company_and_vacancies()

    if(user['subscription_type'] != 'free'):
        # await bot.send_message(callback_qawait bot.send_message(callback_query.from_user.id, f'Total number of job openings in bot:\n<b>{count["total_vacancies"]} jobs from {count["unique_company"]} companies.</b>\nClick on the "?? View Jobs" button or customize your job display by changing categories, keywords, or specific company names.', reply_markup=markup, parse_mode='HTML')uery.from_user.id, f'<b>{count["total_vacancies"]} jobs</b> from <b>{count["unique_company"]} companies</b>.\nClick on the "<i>👁 View Jobs</i>" button or customize your job display by changing categories, keywords, or specific company names.', reply_markup=markup, parse_mode='HTML')
        await bot.send_message(callback_query.from_user.id, f'Total number of job openings in bot:\n<b>{count["total_vacancies"]} jobs from {count["unique_company"]} companies.</b>\nClick on the "👁 View Jobs" button or customize your job display by changing categories, keywords, or specific company names.', reply_markup=markup, parse_mode='HTML')
    else:
        await bot.send_message(callback_query.from_user.id, '👋🏻 Welcome to the Web3 Jobs Bot!\n\n<b>This bot is the best place for professionals looking for web3 jobs!</b>\n\n👀 We monitor companies that have received investments from web3-focused venture capital funds, as well as funds from major crypto ecosystems.\n\n💼 With the help of the bot, you will be able to browse job offers in the professions you are interested in, as well as receive notifications when new job offers appear. Use our bot as an indispensable tool to find your dream job on web3!', reply_markup=markup, parse_mode='HTML')


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_temp[message.from_user.id]=''

    await bot.set_my_commands([
        types.BotCommand("start", "Start bot"),
    ])

    ref_id = decode_payload(message.get_args())
    if(create_user(message.from_user.id, ref_id)):
        send_amplitude_event(message.from_user.id, 'Start')
        return await send_start_msg(message)

    agree = types.InlineKeyboardMarkup(row_width=1)
    agree.add(types.InlineKeyboardButton(text="✅I agree!", callback_data="agree"))
    # print(ref_id)

    await bot.send_message(message.from_user.id, '👁 To start working with the bot, you need to read the user agreement <a href="https://telegra.ph/Terms-of-use-for-jobs-web3-bot-01-28">link</a>. \n\n⚠️ By clicking on the "I agree" button, you confirm that you accept the terms of the user agreement.', reply_markup=agree, parse_mode='HTML', disable_web_page_preview=True)
    send_amplitude_event(message.from_user.id, 'Start')

@dp.message_handler()
async def text_mes(callback_query: types.Message):
    if(callback_query.from_user.id in user_temp):


        if(user_temp[callback_query.from_user.id]=='customize_keywords'):
            update_user_parameter(callback_query.from_user.id, 'keywords', callback_query.text)
        elif(user_temp[callback_query.from_user.id]=='customize_companies'):
            update_user_parameter(callback_query.from_user.id, 'companies', callback_query.text)

        if(user_temp[callback_query.from_user.id] in ['customize_keywords', 'customize_companies']):
            user_temp[callback_query.from_user.id]=''
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(text="Customize job categories for display", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/select_categories.html')))
            markup.add(types.InlineKeyboardButton(text="Customize keywords for displaying vacancies", callback_data="customize_keywords"))
            markup.add(types.InlineKeyboardButton(text="Customize the display of jobs by specific companies", callback_data="customize_companies"))
            markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="job_settings"))
            user = get_user_data(callback_query.from_user.id)
            # await bot.send_message(callback_query.from_user.id, f'You are currently viewing all jobs in the following categories: {user["category"] if user["category"].strip()=="" else "none"}.\n\nAnd also by keywords: {user["keywords"] if user["keywords"].strip()=="" else "none"}\n\nYou can also view all jobs by company: {user["companies"] if user["companies"].strip()=="" else "none"}', reply_markup=markup)
            await bot.send_message(callback_query.from_user.id, f'You are currently viewing all jobs in the following categories: {user["category"] if user["category"].strip()!="" else "none"}.\n\nAnd also by keywords: {user["keywords"] if user["keywords"].strip()!="" else "none"}\n\nYou can also view all jobs by company: {user["companies"] if user["companies"].strip()!="" else "none"}', reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data)
async def process_callback_button(callback_query: types.CallbackQuery):
    await callback_query.answer()
    if callback_query.data == "agree" or callback_query.data == "menu":
        send_amplitude_event(callback_query.from_user.id, 'Agreement_ok')
        await send_start_msg(callback_query)


    elif callback_query.data == "job_settings":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="👨‍💻 Setting up job categories", callback_data="job_categories"))
        markup.add(types.InlineKeyboardButton(text="🔔 Notification settings", callback_data="notification"))
        markup.add(types.InlineKeyboardButton(text="✍️ Write to support", url='https://t.me/Jobs_web3_bot_support'))
        markup.add(types.InlineKeyboardButton(text="🔙 Back to main menu", callback_data="menu"))
        user = get_user_data(callback_query.from_user.id)

        await bot.send_message(callback_query.from_user.id, f'Hello, {callback_query.from_user.first_name}\n\nYour plan: {user["subscription_type"]}\n\nSubscription paid until: {user["subscription_end_date"]}', reply_markup=markup)

    elif callback_query.data in ('clear_companies',"clear_keywords", "job_categories"):
        user_temp[callback_query.from_user.id]=''
        if(callback_query.data == 'clear_keywords'):
            update_user_parameter(callback_query.from_user.id, 'keywords', '')
        if(callback_query.data == 'clear_companies'):
            update_user_parameter(callback_query.from_user.id, 'companies', '')

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="Customize job categories for display", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/select_categories.html')))
        markup.add(types.InlineKeyboardButton(text="Customize keywords for displaying vacancies", callback_data="customize_keywords"))
        markup.add(types.InlineKeyboardButton(text="Customize the display of jobs by specific companies", callback_data="customize_companies"))
        markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="job_settings"))
        user = get_user_data(callback_query.from_user.id)
        # await bot.send_message(callback_query.from_user.id, f'You are currently viewing all jobs in the following categories: {user["category"]}.\n\nAnd also by keywords:  {user["keywords"]}\n\nYou can also view all jobs by company: {user["companies"]}', reply_markup=markup)
        await bot.send_message(callback_query.from_user.id, f'You are currently viewing all jobs in the following categories: {user["category"] if user["category"].strip()!="" else "none"}.\n\nAnd also by keywords: {user["keywords"] if user["keywords"].strip()!="" else "none"}\n\nYou can also view all jobs by company: {user["companies"] if user["companies"].strip()!="" else "none"}', reply_markup=markup)



    # Добавляем кнопки "Clear keywords list" и "Clear companies list"
    elif callback_query.data == "customize_keywords":
        keyboard = InlineKeyboardMarkup()
        clear_keywords_button = InlineKeyboardButton("Clear keywords list", callback_data="clear_keywords")
        keyboard.add(clear_keywords_button)
        user_temp[callback_query.from_user.id]='customize_keywords'
        await bot.send_message(callback_query.from_user.id, f'Customize keywords for displaying vacancies.\n\nIf you find it inconvenient to view jobs by category, enter the keywords you want to search by. If you need to enter more than one word, please separate them with commas.', reply_markup=keyboard)


    elif callback_query.data == "customize_companies":
        keyboard = InlineKeyboardMarkup()
        clear_companies_button = InlineKeyboardButton("Clear companies list", callback_data="clear_companies")
        keyboard.add(clear_companies_button)
        user_temp[callback_query.from_user.id]='customize_companies'
        await bot.send_message(callback_query.from_user.id, f'Customize the display of jobs by specific companies\n\nIf you do not want to see the job openings for the companies you are interested in, please enter their names. You will see all the job openings of those companies. If you are interested in multiple companies, please enter their names separated by commas.', reply_markup=keyboard)


    elif callback_query.data == "customize_keywords":
        await bot.send_message(callback_query.from_user.id, f'Customize keywords for displaying vacancies.\n\nIf you find it inconvenient to view jobs by category, enter the keywords you want to search by. If you need to enter more than one word, please separate them with commas.')
        user_temp[callback_query.from_user.id]='customize_keywords'

    elif callback_query.data == "customize_companies":
        await bot.send_message(callback_query.from_user.id, f'Customize the display of jobs by specific companies\n\nIf you do not want to see the job openings for the companies you are interested in, please enter their names. You will see all the job openings of those companies. If you are interested in multiple companies, please enter their names separated by commas.')
        user_temp[callback_query.from_user.id]='customize_companies'

    elif "notification" in callback_query.data:
        off_text = 'Your notifications are currently turned off.\n\nIf you turn them on, you will receive notifications about all new job listings from the categories, companies, and keywords you have set up in the Display Categories, Companies, and Keywords sections.'
        off_markup = types.InlineKeyboardMarkup(row_width=1)
        off_markup.add(types.InlineKeyboardButton(text="🔔 Turn on notifications", callback_data="on_notifications"))
        off_markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="job_settings"))
        # (если включены)
        on_text = 'Your notifications are currently turned on.\n\nIf you want to stop receiving them, tap on the ‘Turn Off Notifications’ button.'
        on_markup = types.InlineKeyboardMarkup(row_width=1)
        on_markup.add(types.InlineKeyboardButton(text="🔕 Turn off notifications", callback_data="off_notifications"))
        on_markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="job_settings"))

        notification = get_user_data(callback_query.from_user.id)['notification']

        if('off' in callback_query.data):
            update_user_parameter(callback_query.from_user.id, 'notification', 0)
        if('on' in callback_query.data):
            update_user_parameter(callback_query.from_user.id, 'notification', 1)

        if(notification==0):
            await bot.send_message(callback_query.from_user.id, off_text, reply_markup=off_markup)
        else:
            await bot.send_message(callback_query.from_user.id, on_text, reply_markup=on_markup)



    elif callback_query.data == 'reflink':
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="Set up a withdrawal wallet", callback_data="pass"))
        markup.add(types.InlineKeyboardButton(text="Request withdrawal", callback_data="pass"))
        markup.add(types.InlineKeyboardButton(text="View withdrawal history", callback_data="pass"))
        markup.add(types.InlineKeyboardButton(text="🔙 Back to main menu", callback_data="menu"))
        user = get_user_data(callback_query.from_user.id)
        ref_url = await get_start_link(str(callback_query.from_user.id), encode=True)
        ref_count = count_referrals(callback_query.from_user.id)
        await bot.send_message(callback_query.from_user.id,  f'Join our referral program and earn 50% of all sales made via your referral link!\n\nYour reflink: {ref_url} \nReferrals: {ref_count}\nBalance {user["balance"]}', reply_markup=markup)



def send_amplitude_event( user_id, event_type, event_properties=None):
    def send_data(user_id, event_type, event_properties):
        global lock
        url = "https://api.amplitude.com/2/httpapi"
        with lock:
            user_data = get_user_data(user_id)
        registration_date = datetime.strptime(user_data['registration_date'], '%Y-%m-%d')
        cohort_year = registration_date.year
        cohort_month = registration_date.month
        cohort_week = registration_date.isocalendar()[1]  # Получаем номер недели
        cohort_day = registration_date.timetuple().tm_yday  # Получаем номер дня в году
        referral = user_data['ref_id'] if user_data['ref_id'] else ''
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        event = {
            "api_key": 'e0d57919c56bbf7e8555c602c3c0dcd5',
            "events": [
                {
                    "user_id": user_id,
                    "event_type": event_type,
                    'event_properties': {
                        'cohort_year': cohort_year,
                        'cohort_month': cohort_month,
                        'cohort_week': cohort_week,
                        'cohort_day': cohort_day,
                        'referral': referral
                    }
                }
            ]
        }
        if event_properties:
            event.update(event_properties)
        response = requests.post(url,headers=headers, data=json.dumps(event))
    t = Thread(target=send_data, args=(user_id, event_type, event_properties))
    t.start()



async def choose_your_dinner():
    # print(123)
    users = get_users_with_expired_subscription()
    for user in users:
        if(user['subscription_type'] == 'trial'):
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(text="👛 Pay for your subscription right now!", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/subscribtion.html')))
            await bot.send_message(user['telegram_id'],  f'<b>⚠️ Your 5-day trial period has expired!</b> Pay for your subscription right now to continue using the bot!', reply_markup=markup, parse_mode="HTML")
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(text="👛 Pay for your subscription right now!", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/subscribtion.html')))
            await bot.send_message(user['telegram_id'],  f'⚠️ Your paid subscription has expired! Pay for a new subscription to continue using the bot!', reply_markup=markup)

    msg = get_earliest_message()
    if(msg!=None):
        for key in msg:
            if(msg[key] == True):
                users = get_user_with_parameter('subscription_type', key)
                if(users):
                    for user in users:
                        try:
                            if(msg['image_path'] == ''):
                                await bot.send_message(user[0], msg['msg'], parse_mode="HTML")
                            else:
                                photo = InputFile(msg['image_path'])
                                await bot.send_photo(user[0], photo=photo, caption=msg['msg'], parse_mode="HTML")
                        except Exception as e:
                            print(e)


async def choose_your_dinner24():
    users = get_users_subscription_expired_days()
    for user in users:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="👛 Pay for your subscription right now!", web_app=WebAppInfo(url=f'https://testserverkursk.ru:8085/subscribtion.html')))
        await bot.send_message(user['telegram_id'],  f'⚠️ 10 new jobs were found in the categories of your choice since your subscription ended! Pay for your subscription right now to continue using the bot!', reply_markup=markup)


async def scheduler():
    while True:
        asyncio.create_task(choose_your_dinner())
        await asyncio.sleep(5)

async def scheduler24():
    while True:
        asyncio.create_task(choose_your_dinner24())
        await asyncio.sleep(24*60*60)



async def on_startup(dp):
    asyncio.create_task(scheduler())
    asyncio.create_task(scheduler24())

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

# if __name__ == '__main__':
#     executor.start_polling(dp, skip_updates=True)
