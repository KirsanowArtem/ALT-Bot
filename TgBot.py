import asyncio
import nest_asyncio
import os
import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ContextTypes
from telegram import ChatPermissions
from datetime import datetime, timedelta

nest_asyncio.apply()

CREATOR_CHAT_ID = -1002340443739
sent_messages = {}
muted_users = {}
users_info = {}
admins = []
programmers = ["ArtemKirss"]
total_score = 0
num_of_ratings = 0
photo_sending = False
BOTTOCEN = "8039978006:AAEpV8GeHHyxcl-wx-nXyTIuisLKBTsJRGs"


def get_current_time_kiev():
    kiev_tz = pytz.timezone('Europe/Kiev')
    now = datetime.now(kiev_tz)
    return now.strftime("%H:%M; %d/%m/%Y")


async def start(update: Update, context):
    user = update.message.from_user
    chat_id = update.effective_chat.id

    if chat_id == -1002340443739:
        await update.message.reply_text("Команда /start недоступна в цій групі.")
        return

    if user.id not in users_info:
        users_info[user.id] = {
            'join_date': get_current_time_kiev(),
            'rating': 0
        }

    keyboard = [
        ["/start", "/rate"],
        ["/massage", "/stopmassage"],
        ["/fromus", "/help"],
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Привіт! Я ваш бот. Введіть команду /rate для залишення відгуку, /massage для зв'язку з адміністраторами або /help для ознайомлення з командами.",
        reply_markup=reply_markup
    )


async def rate(update: Update, context):
    user_id = update.message.from_user.id

    if user_id in users_info:
        user_rating = users_info[user_id]['rating']
    else:
        user_rating = None

    total_score = sum(user_data['rating'] for user_data in users_info.values())
    num_of_ratings = len(users_info)

    if num_of_ratings > 0:
        average_rating = total_score / num_of_ratings
    else:
        average_rating = 0

    rating_text = f"Загальна оцінка: {round(average_rating, 1)}⭐️\nВаша попередня оцінка: {user_rating}⭐️"

    keyboard = [
        [InlineKeyboardButton("0.5⭐️", callback_data='0.5'), InlineKeyboardButton("1⭐️", callback_data='1')],
        [InlineKeyboardButton("1.5⭐️", callback_data='1.5'), InlineKeyboardButton("2⭐️", callback_data='2')],
        [InlineKeyboardButton("2.5⭐️", callback_data='2.5'), InlineKeyboardButton("3⭐️", callback_data='3')],
        [InlineKeyboardButton("3.5⭐️", callback_data='3.5'), InlineKeyboardButton("4⭐️", callback_data='4')],
        [InlineKeyboardButton("4.5⭐️", callback_data='4.5'), InlineKeyboardButton("5⭐️", callback_data='5')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)


    await update.message.reply_text(f"{rating_text}\nОберіть оцінку:", reply_markup=reply_markup)


async def button_callback(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    rating = float(query.data)

    if user_id in users_info:
        users_info[user_id]['rating'] = rating
    else:
        users_info[user_id] = {'join_date': datetime.now(), 'rating': rating}

    total_score = sum(user_data['rating'] for user_data in users_info.values())

    num_of_ratings = len(users_info)
    average_rating = total_score / num_of_ratings if num_of_ratings > 0 else 0


    await query.edit_message_text(f"Загальна оцінка: {round(average_rating, 1)}⭐️\nВаша оцінка: {rating}⭐️\nДякуємо за вашу оцінку!")


async def button(update: Update, context):
    global total_score, num_of_ratings

    query = update.callback_query
    await query.answer()

    selected_rate = float(query.data)
    total_score += selected_rate
    num_of_ratings += 1

    average_rating = total_score / num_of_ratings

    user_id = query.from_user.id
    if user_id in users_info:
        users_info[user_id]['rating'] = selected_rate

    await query.edit_message_text(
        f"Дякуємо за ваш відгук! Ваша оцінка: {selected_rate}⭐️\nЗагальна оцінка: {round(average_rating, 1)}⭐️")


async def auto_delete_message(bot, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


async def massage(update: Update, context):
    user_id = update.message.from_user.id
    if user_id in muted_users and muted_users[user_id]['expiration'] > datetime.now():
        reply = await update.message.reply_text("Ви замучені й не можете надсилати повідомлення.")
        asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
        return
    reply = await update.message.reply_text(
        "Введіть ваше повідомлення, і його буде надіслано адміністраторам бота. Введіть /stopmassage, щоб завершити введення повідомлень."
    )

    context.user_data['waiting_for_message'] = True

    asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=5))


async def stopmassage(update: Update, context):
    if context.user_data.get('waiting_for_message'):
        reply = await update.message.reply_text("Ви завершили введення повідомлень.")
        context.user_data['waiting_for_message'] = False
        asyncio.create_task(
            auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=5))
    else:
        await update.message.reply_text("Ви не перебуваєте в режимі введення повідомлень.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != CREATOR_CHAT_ID:
        user_id = update.message.from_user.id
        if user_id in muted_users and muted_users[user_id]['expiration'] > datetime.now():
            reply = await update.message.reply_text("Ви замучені й не можете надсилати повідомлення.")
            asyncio.create_task(
                auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
            return

        if context.user_data.get('waiting_for_message'):
            user_name = update.effective_user.first_name
            user_username = update.effective_user.username if update.effective_user.username else "немає імені користувача"
            current_time = get_current_time_kiev()
            user_message = ""
            first_message = f'Повідомлення від "{user_name}"; "@{user_username}" \n{current_time}:'

            if update.message.text:
                user_message = update.message.text
                first_message += f'\n{user_message}'

            if update.message.photo:
                photo_file_id = update.message.photo[-1].file_id
                message_to_admin = await context.bot.send_photo(chat_id=CREATOR_CHAT_ID, photo=photo_file_id, caption=first_message)

            elif update.message.document:
                document_file_id = update.message.document.file_id
                document_name = update.message.document.file_name
                message_to_admin = await context.bot.send_document(chat_id=CREATOR_CHAT_ID, document=document_file_id, caption=first_message)

            else:
                message_to_admin = await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=first_message)

            sent_messages[message_to_admin.message_id] = update.effective_user.id

            reply = await update.message.reply_text("Ваше повідомлення надіслано адміністраторам бота.")
            asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=5))
        else:
            await update.message.reply_text("Введіть /massage, щоб надіслати повідомлення адміністраторам бота.")
    else:
        if update.effective_user.id != context.bot.id:
            if update.message.reply_to_message:
                if update.message.reply_to_message.from_user.id == context.bot.id:
                    original_message_id = update.message.reply_to_message.message_id
                    if original_message_id in sent_messages:
                        original_user_id = sent_messages[original_message_id]

                        reply_text = update.message.text if update.message.text else ""

                        if update.message.photo:
                            photo_file_id = update.message.photo[-1].file_id
                            await context.bot.send_photo(chat_id=original_user_id, photo=photo_file_id, caption=reply_text)

                        elif update.message.document:
                            document_file_id = update.message.document.file_id
                            document_name = update.message.document.file_name
                            await context.bot.send_document(chat_id=original_user_id, document=document_file_id, caption=reply_text)
                        else:
                            await context.bot.send_message(chat_id=original_user_id, text=reply_text)


async def mute(update: Update, context):
    if update.message.chat.id != CREATOR_CHAT_ID:
        reply = await update.message.reply_text("Ця команда доступна тільки адміністраторам бота.")
        asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
        return

    if len(context.args) < 2:
        reply = await update.message.reply_text("Використовуйте: /mute <час> <користувач> [причина]")
        asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=60))
        return

    mute_time = 0
    username = None
    reason = "По рішенню администратора"
    for arg in context.args:
        if arg.startswith('@'):
            username = arg[1:]
        elif ':' in arg or '\\' in arg:
            time_parts = arg.replace('\\', ':').split(':')
            time_parts = [int(part) for part in time_parts]
            if len(time_parts) == 3:
                mute_time += timedelta(hours=time_parts[0], minutes=time_parts[1], seconds=time_parts[2]).total_seconds()
            elif len(time_parts) == 2:
                mute_time += timedelta(minutes=time_parts[0], seconds=time_parts[1]).total_seconds()
            elif len(time_parts) == 1:
                mute_time += timedelta(seconds=time_parts[0]).total_seconds()
        else:
            reason = arg

    if username is None:
        await update.message.reply_text("Не вказано користувача для мута.")
        return

    user_id = None

    for message_id, id in sent_messages.items():
        user_info = await context.bot.get_chat_member(chat_id=CREATOR_CHAT_ID, user_id=id)
        if user_info.user.username and user_info.user.username.lower() == username.lower():
            user_id = id
            break

    if user_id is not None:
        chat_member = await context.bot.get_chat_member(chat_id=CREATOR_CHAT_ID, user_id=user_id)

        if chat_member.status == "creator":
            reply = await update.message.reply_text(f"Невозможно замутить владельца чата.")
            asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=60))
            return

        if mute_time == 0:
            mute_time = 300

        mute_duration = str(timedelta(seconds=mute_time))

        muted_users[user_id] = {
            'expiration': datetime.now() + timedelta(seconds=mute_time),
            'reason': reason
        }

        mute_permissions = ChatPermissions(can_send_messages=False)

        await context.bot.restrict_chat_member(chat_id=CREATOR_CHAT_ID, user_id=user_id, permissions=mute_permissions)
        await context.bot.send_message(chat_id=user_id, text=f"Вас замутили на {mute_duration}\nПричина: {reason}")
        reply = await update.message.reply_text(f"Користувач @{username} замучен на {mute_duration}\nПричина: {reason}")
        asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=60))
    else:
        reply = await update.message.reply_text(f"Користувач @{username} не знайден.")
        asyncio.create_task(auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=60))

async def unmute(update: Update, context):
    user = update.message.from_user.username
    if not is_programmer(user) and not is_admin(user):
            reply = await update.message.reply_text("Ця команда доступна тільки адміністраторам бота..")
            asyncio.create_task(
                auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
            return

    if len(context.args) < 1:
        await update.message.reply_text("Використовуйте: /unmute <користувач>")
        return

    username = context.args[0].lstrip('@')
    user_id = None

    for message_id, id in sent_messages.items():
        user_info = await context.bot.get_chat_member(chat_id=CREATOR_CHAT_ID, user_id=id)
        if user_info.user.username and user_info.user.username.lower() == username.lower():
            user_id = id
            break

    if user_id is not None and user_id in muted_users:
        del muted_users[user_id]
        await context.bot.send_message(chat_id=user_id, text=f"Ви були розмучені.")
        await update.message.reply_text(f"Користувач @{username} був розмучений.")
    else:
        await update.message.reply_text(f"Користувач @{username} не знайдений або не був замучений.")


async def mutelist(update: Update, context):
    user = update.message.from_user.username
    if update.message.chat.id != CREATOR_CHAT_ID:
        if not is_programmer(user) and not is_admin(user):
            reply = await update.message.reply_text("Ця команда доступна тільки адміністраторам бота.")
            asyncio.create_task(
                auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
            return

    response = "Замучені користувачі:\n"

    if muted_users:
        for user_id, mute_info in muted_users.items():
            expiration = mute_info['expiration']
            time_left = expiration - datetime.now()
            reason = mute_info['reason']

            user_info = await context.bot.get_chat_member(chat_id=CREATOR_CHAT_ID, user_id=user_id)
            user_fullname = user_info.user.first_name or "Невідомий"
            username = user_info.user.username or "Немає імені користувача"

            user_data = users_info.get(user_id, {})
            join_date = user_data.get('join_date', 'Невідома')
            rating = user_data.get('rating', 0)
            mute_symbol = "🔇"

            admins_sumdol = "👨🏻‍💼"

            if username in admins:
                admins_sumdol = "👮🏻‍♂️️"

            if username in programmers:
                admins_sumdol = "👨🏻‍💻"

            response += (
                f"{admins_sumdol} {mute_symbol} {user_fullname}; @{username}\n"
                f"Осталось: {str(time_left).split('.')[0]}\n"
                f"Причина: {reason}\n"
                f"Дата захода: {join_date}\n"
                f"Оцінка: {rating}⭐️\n"
                "-------------------------------------------------------------------------\n"
            )
    else:
        response += "Немає замучених користувачів.\n"
        response += "-------------------------------------------------------------------------\n"

    await update.message.reply_text(response)


async def alllist(update: Update, context):
    user = update.message.from_user.username
    if update.message.chat.id != CREATOR_CHAT_ID:
        if not is_programmer(user) and not is_admin(user):
            reply = await update.message.reply_text("Ця команда доступна тільки адміністраторам бота.")
            asyncio.create_task(
                auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
            return

    response = "Користувачі:\n"

    unique_users = set()

    for message_id, user_id in sent_messages.items():
        unique_users.add(user_id)

    if unique_users:
        for user_id in unique_users:
            user_info = await context.bot.get_chat_member(chat_id=CREATOR_CHAT_ID, user_id=user_id)
            user_fullname = user_info.user.first_name or "Невідомий"
            username = user_info.user.username or "Немає імені користувача"

            user_data = users_info.get(user_id, {})
            join_date = user_data.get('join_date', 'Невідома')
            rating = user_data.get('rating', 0)

            admins_sumdol = "👨🏻‍💼"

            if username in admins:
                admins_sumdol = "👮🏻‍♂️️"

            if username in programmers:
                admins_sumdol = "👨🏻‍💻"


            if user_id in muted_users:
                mute_symbol = "🔇"
            else:
                mute_symbol = "🔊"
            response += f"{admins_sumdol} {mute_symbol} {user_fullname}; @{username}\nДата захода: {join_date}\nОцінка: {rating}⭐️\n"
            response += "-------------------------------------------------------------------------\n"
    else:
        response += "Немає користувачів.\n"
        response += "-------------------------------------------------------------------------\n"

    response += "Замучені користувачі:\n"

    if muted_users:
        for user_id, mute_info in muted_users.items():
            expiration = mute_info['expiration']
            time_left = expiration - datetime.now()
            reason = mute_info['reason']
            user_info = await context.bot.get_chat_member(chat_id=CREATOR_CHAT_ID, user_id=user_id)
            user_fullname = user_info.user.first_name or "Невідомий"
            username = user_info.user.username or "Немає імені користувача"

            user_data = users_info.get(user_id, {})
            join_date = user_data.get('join_date', 'Невідома')
            rating = user_data.get('rating', 0)

            admins_sumdol = "👨🏻‍💼"

            if username in admins:
                admins_sumdol = "👮🏻‍♂️️"

            if username in programmers:
                admins_sumdol = "👨🏻‍💻"

            response += (
                f"{admins_sumdol} {mute_symbol} {user_fullname}; @{username}\n"
                f"Залишилось: {str(time_left).split('.')[0]}\n"
                f"Причина: {reason}\n"
                f"Дата захода: {join_date}\n"
                f"Оцінка: {rating}⭐️\n"
                "-------------------------------------------------------------------------\n"
            )
    else:
        response += "Немає замучених користувачів.\n"
        response += "-------------------------------------------------------------------------\n"

    await update.message.reply_text(response)


async def allmassage(update: Update, context):
    user = update.message.from_user.username
    if update.message.chat.id != CREATOR_CHAT_ID:
        if not is_programmer(user) and not is_admin(user):
            reply = await update.message.reply_text("Ця команда доступна тільки адміністраторам бота.")
            asyncio.create_task(
                auto_delete_message(context.bot, chat_id=reply.chat.id, message_id=reply.message_id, delay=10))
            return

    if not context.args:
        await update.message.reply_text("Будь ласка, вкажіть текст повідомлення після команди.")
        return

    message_text = ' '.join(context.args)
    unique_users = set(sent_messages.values())

    for user_id in unique_users:
        await context.bot.send_message(chat_id=user_id, text=message_text)

    await update.message.reply_text("Повідомлення відправлено всім користувачам.")


async def help(update: Update, context):
    if update.message.chat.id == CREATOR_CHAT_ID:
        help_text = (
            "Доступні команди в групі:\n"
            "Відповісти на повідомлення бота - Відправити повідомлення користувачу який прислав це повідомлення.\n"
            "/mute <час> <користувач> [причина] - Замучити користувача на вказаний час.\n"
            "/unmute <користувач> - Розмутити користувача.\n"
            "/mutelist - Показати список замучених користувачів.\n"
            "/alllist - Показати всіх користувачів.\n"
            "/allmassage <повідомлення> - Надіслати повідомлення всім користувачам.\n"
        )
    else:
        help_text = (
            "Доступні команди в боті:\n"
            "/start - Запустити бота.\n"
            "/rate - Залишити відгук.\n"
            "/massage - Почати введення повідомленнь адміністраторам.\n"
            "/stopmassage - Завершити введення повідомлень.\n"
            "/fromus - інформація про нас\n"
            "/help - Показати доступні команди.\n"
        )

    await update.message.reply_text(help_text)


async def fromus(update: Update, context):
    await update.message.reply_text(
        "*Ми команда ALT, до нас входять:*",
        parse_mode="MarkdownV2"
    )
    await update.message.reply_text(
        "*Кірсанов Артем*",
        parse_mode="MarkdownV2"
    )
    await update.message.reply_text("🔷Робив проєкти:\n🔹Гра\n🔹Бот підтримки\n🔶Робив міні-проєкти:\n🔸міні-гра палички\n🔈Посиланняна на контакти/соцмережі:\n----")
    await update.message.reply_text(
        "*Дорошенко Леонід*",
        parse_mode="MarkdownV2"
    )
    await update.message.reply_text("🔷Робив проєкти:\n🔹Гра\n🔶Робив міні-проєкти:\n🔸міні-гра палички\n🔈Посиланняна на контакти/соцмережі:\n----")
    await update.message.reply_text(
        "*Гандзий Егор*",
        parse_mode="MarkdownV2"
    )
    await update.message.reply_text("🔷Робив проєкти:\n🔹---\n🔶Робив міні-проєкти:\n🔸міні-гра палички\n🔈осиланняна на контакти/соцмережі:\n----")
    await update.message.reply_text(
        "*Попов Олексій*",
        parse_mode="MarkdownV2"
    )
    await update.message.reply_text("🔷Робив проєкти:\n🔹Гра\n🔶Робив міні-проєкти:\n🔸---\n🔈Посиланняна на контакти/соцмережі:\n----")


def is_programmer(user):
    return user in programmers


def is_admin(user):
    return user in admins



async def admin(update: Update, context: CallbackContext):
    if context.args:
        target_user = context.args[0]
        user = update.message.from_user.username

        if is_programmer(user):
            if target_user not in admins:
                admins.append(target_user)
                await update.message.reply_text(f"Пользователь {target_user} добавлен в список администраторов.")
            else:
                await update.message.reply_text(f"Пользователь {target_user} уже является администратором.")
        else:
            await update.message.reply_text("Эту команду могут выполнять только программисты.")
    else:
        await update.message.reply_text("Пожалуйста, укажите имя пользователя после команды.")

async def deleteadmin(update: Update, context: CallbackContext):
    if context.args:
        target_user = context.args[0]
        user = update.message.from_user.username

        if is_programmer(user):
            if target_user in admins:
                admins.remove(target_user)
                await update.message.reply_text(f"Пользователь {target_user} удалён из списка администраторов.")
            else:
                await update.message.reply_text(f"Пользователь {target_user} не является администратором.")
        else:
            await update.message.reply_text("Эту команду могут выполнять только программисты.")
    else:
        await update.message.reply_text("Пожалуйста, укажите имя пользователя после команды.")



async def programier(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    if is_programmer(user):
        if len(context.args) > 0:
            new_programmer = context.args[0].replace("@", "")
            if new_programmer not in programmers:
                programmers.append(new_programmer)
                await update.message.reply_text(f"Пользователь {new_programmer} добавлен в список программистов.")
            else:
                await update.message.reply_text(f"Пользователь {new_programmer} уже в списке программистов.")
        else:
            await update.message.reply_text("Используйте: /p @username")
    else:
        await update.message.reply_text("Эту команду могут выполнять только программисты.")


async def deleteprogramier(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    if is_programmer(user):
        if len(context.args) > 0:
            removed_programmer = context.args[0].replace("@", "")
            if removed_programmer == "ArtemKirss":
                await update.message.reply_text(f"Нельзя удалить {removed_programmer} из списка программистов.")
            elif removed_programmer in programmers:
                programmers.remove(removed_programmer)
                await update.message.reply_text(f"Пользователь {removed_programmer} удалён из списка программистов.")
            else:
                await update.message.reply_text(f"Пользователь {removed_programmer} не является программистом.")
        else:
            await update.message.reply_text("Используйте: /unp @username")
    else:
        await update.message.reply_text("Эту команду могут выполнять только программисты.")


async def o(update: Update, context: CallbackContext):
    programmer_list = "\n".join(programmers) if programmers else "Список программистов пуст."
    admin_list = "\n".join(admins) if admins else "Список администраторов пуст."
    await update.message.reply_text(f"Программисты:\n{programmer_list}\n\nАдминистраторы:\n{admin_list}")



def main():
    application = Application.builder().token(BOTTOCEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rate", rate))
    application.add_handler(CommandHandler("massage", massage))
    application.add_handler(CommandHandler("stopmassage", stopmassage))
    application.add_handler(CommandHandler("fromus", fromus))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CommandHandler("mutelist", mutelist))
    application.add_handler(CommandHandler("alllist", alllist))
    application.add_handler(CommandHandler("allmassage", allmassage))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("deleteadmin", deleteadmin))
    application.add_handler(CommandHandler("programier", programier))
    application.add_handler(CommandHandler("deleteprogramier", deleteprogramier))
    application.add_handler(CommandHandler("o", o))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, handle_message))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())