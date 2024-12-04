from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile, ContentType
from peewee import *
import io
import emoji
import asyncio
from datetime import *

from keyboards import *
from database.models import *
from handlers.registration import us_name, us_age, us_sex, us_inf, ph, ch_us_sex
from ProfileStatesGroup import *


TOKEN_API = " "

bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=MemoryStorage())

user_id = None

db.connect()
@dp.message_handler(commands=['myprofile', 'start'])
async def profile(message: types.Message):
    global user_id

    user_id = message.from_user.id
    user_exists = Users.select().where(Users.id == user_id).exists()
    if user_exists:
        asyncio.create_task(send_notification(user_id))
        asyncio.create_task(delete_watched_and_liked_forms())

        user = Users.get(Users.id == message.from_user.id)
        photo = user.photo
        input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")
        if user.information != None:
            form = f"{user.name}, {user.age}"
        else:
            form = f"{user.name}, {user.age}"
        await bot.send_photo(chat_id=message.from_user.id, photo=input_file, caption=form)        

        text = "1. Заполнить анкету заново " + emoji.emojize(":writing_hand:") + "\n2. Изменить фото " + emoji.emojize(":sunglasses:") + "\n3. Изменить текст анкеты " + emoji.emojize(":pencil:") + "\n4. Смотреть анкеты " + emoji.emojize(":red_heart:")
        await message.answer(text=text, reply_markup=edit_form)
        await ProfileStatesGroup.choice.set()
    else:
        await message.answer(text="Нужно заполнить анкету" + emoji.emojize(":bust_in_silhouette:") + "\nВведите ваше имя:")
        await ProfileStatesGroup.name.set()


@dp.message_handler(lambda message: message.text.startswith("/"), state="*")
async def handle_global_commands(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await notifications(message)


async def send_notification(user_id):
    while True:
        if user_id is not None:
            liked_user = Liked_Users.select().where((Liked_Users.liked_id == user_id) & (Liked_Users.watched == False)).exists()
            if liked_user:
                await bot.send_message(chat_id=user_id, text="Вами кто-то заинтересовался! <b>/notifications</b>", parse_mode='HTML')
                await bot.send_sticker(user_id, sticker="CAACAgIAAxkBAAJmwmV2_yoeM5djzCP_Rg1ssho3ZPrHAAJtJQAC9LgoSjiBlNxAD-u8MwQ")
                Liked_Users.update(watched=True).where(Liked_Users.liked_id == user_id).execute()
        await asyncio.sleep(5)

async def delete_watched_and_liked_forms():
    while True:
        today = datetime.now().date()
        two_days = timedelta(days=2)
        d = today-two_days
        l_user = Liked_Users.select().where(Liked_Users.date == d).exists()
        if l_user:
            Liked_Users.delete().where(Liked_Users.date == d).execute()
        await asyncio.sleep(5)


@dp.message_handler(state=ProfileStatesGroup.choice)
async def choice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['choice'] = message.text
        if data['choice'] == "1":
            name = Users.get(Users.id == message.from_user.id)
            your_name = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            your_name.add(KeyboardButton(text=name.name))

            await message.answer("Введи своё имя:", reply_markup=your_name)
            await ProfileStatesGroup.name.set()
        if data['choice'] == "2":
            await message.answer("Отправь своё фото")
            await ProfileStatesGroup.photo.set()
        if data['choice'] == "3":
            await message.answer("Напиши что-нибудь о себе:")
            await ProfileStatesGroup.inf.set()
        if data['choice'] == "4":
            await ProfileStatesGroup.search.set()
            await search(message, state)


@dp.message_handler(state=ProfileStatesGroup.name)
async def user_name(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    else:
        async with state.proxy() as data:
            data['name'] = message.text
            await us_name(message)
            await ProfileStatesGroup.age.set()


@dp.message_handler(state=ProfileStatesGroup.age)
async def user_age(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    else:
        async with state.proxy() as data:
            data['age'] = message.text

            try:
                if (26 >= int(message.text) >= 16):
                        await us_age(message)
                        await ProfileStatesGroup.sex.set()
                else:
                    await message.answer(text='Извините, но вы не должны быть младше 16 и старше 26 лет.\nПопробуйте ещё раз:')
                    await ProfileStatesGroup.age.set()
            except:
                await message.answer(text='Возраст введён неверно..\nПопробуйте ещё раз:')


@dp.message_handler(state=ProfileStatesGroup.sex)
async def user_sex(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    else:
        async with state.proxy() as data:
            data['sex'] = message.text
            i = 0
            i = await us_sex(message, i)
            if i == 0:
                await ProfileStatesGroup.sex.set() 
            if i == 1:
                await ProfileStatesGroup.inf.set()
            k = i


@dp.message_handler(state=ProfileStatesGroup.inf)
async def user_inf(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    else:
        async with state.proxy() as data:
            data['inf'] = message.text
            i = k

            k = await us_inf(message, i)
            if k == 3: await state.finish()
            else:
                await ProfileStatesGroup.photo.set()
                await bot.send_sticker(message.from_user.id, sticker="CAACAgIAAxkBAAJmwGV2_pqEwnIwZbRG48BJSVCbVATkAAJfEwACLl7IS9mrvzBghJYzMwQ")
            

@dp.message_handler(state=ProfileStatesGroup.photo, content_types=ContentType.PHOTO)
async def user_photo(message: types.Message, state: FSMContext):
    global k
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    else:
        async with state.proxy() as data:
            if message.content_type == "photo":
                await state.finish()

                photo_binary = io.BytesIO()
                await message.photo[-1].download(photo_binary)
                data['photo'] = photo_binary.getvalue()
                photo = data['photo']

                j = k
                k = await ph(message, photo, j)
                await ProfileStatesGroup.user_sex.set()
                await message.answer("Кого хочешь искать?", reply_markup=another_user_sex)
 

@dp.message_handler(state=ProfileStatesGroup.user_sex)
async def choose_user_sex(message: types.Message, state: FSMContext):
    if message.text == "/myprofile":
        await profile(message)
    elif message.text == "/notifications":
        await message.answer("Нельзя посмотреть уведомления во время создания анкеты.")
    else:
        k = 0
        k = await ch_us_sex(message, k)

        if k == 1:
            await message.answer("Твоя анкета успешно создана!", reply_markup=my_profile)


@dp.message_handler(state=ProfileStatesGroup.search)
async def search(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        me = Users.get(Users.id == message.from_user.id)
        another_user_query = Users.select().where(
            Users.sex == me.fav_sex,
            Users.fav_sex == me.sex,
            Users.age <= me.age + 3
        )

        if another_user_query.exists():
            for another_user in another_user_query:
                liked_user_exists = Liked_Users.select().where(
                    Liked_Users.user == me.id,
                    Liked_Users.liked_id == another_user.id
                ).exists()

                if not liked_user_exists:
                    photo = another_user.photo
                    input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")

                    if another_user.information is None:
                        form = f"{another_user.name}, {another_user.age}"
                    else:
                        form = f"{another_user.name}, {another_user.age}\n{another_user.information}"

                    await bot.send_photo(
                        chat_id=message.from_user.id,
                        photo=input_file,
                        caption=form,
                        reply_markup=like_dislike
                    )

                    if message.text == emoji.emojize(":red_heart:"):
                        Liked_Users.create(
                            user=me.id,
                            liked_id=another_user.id,
                            date=datetime.today()
                        )
                    break

            else:
                await message.answer("Подходящих пользователей не найдено")
        else:
            await message.answer("Подходящих пользователей не найдено")


            



lu = None # id лайкнувшего пользователя
step = None
@dp.message_handler(commands=['notifications'])
async def notifications(message: types.Message):
    global step
    if message.text == "/myprofile":
        await profile(message)
    else:
        global lu
        liked_user = Liked_Users.select().where(Liked_Users.liked_id == message.from_user.id).exists()
        if liked_user:
            liked_user = Liked_Users.get(Liked_Users.liked_id == message.from_user.id)
            user = Users.get(Users.id == liked_user.user)

            photo = user.photo
            input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")
            if user.information == None:
                form = f"{user.name}, {user.age}"
            else: 
                form = f"{user.name}, {user.age}\n{user.information}"
            await bot.send_photo(chat_id=message.from_user.id, photo=input_file, caption=form)
        
            lu = user.id

            if liked_user.mutually == False:
                l_d = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                l_d.add(
                    KeyboardButton(text=emoji.emojize(":thumbs_down:")),
                    KeyboardButton(text=emoji.emojize(":red_heart:"))
                )
                await message.answer(text="Выбери действие:", reply_markup=l_d)
                await ProfileStatesGroup.choice.set()
            else:
                chat_id = message.from_user.id
                link = f"https://t.me/{user.name_tg}"
                user_profile_link = f"Приятного общения с {link}!"
                await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")

                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == message.from_user.id)).execute()
                Liked_Users.delete().where((Liked_Users.user == message.from_user.id) & (Liked_Users.liked_id == user.id)).execute()
                step = "next_form"
        else:
            await message.answer(text="Пока что у тебя нет уведомлений", reply_markup=types.ReplyKeyboardRemove())
            await bot.send_sticker(message.from_user.id, sticker="CAACAgIAAxkBAAJmvmV2_K91_LwCwP_yQcYVqOKlYj8iAALGFAACckXQS2ucYVpYIo33MwQ")


@dp.message_handler(state=ProfileStatesGroup.choice)
async def notification(message: types.Message, state=FSMContext):
    global lu, step
    step = None
    async with state.proxy() as data:
        data['choice'] = message.text

        if message.text == "/myprofile":
            await profile(message)
        elif message.text == "/notifications":
            await notifications(message)
        else:
            if message.text == emoji.emojize(":thumbs_down:"):
                user = Users.get(Users.id == lu)
                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == message.from_user.id)).execute()
                step = "next_form"
                lu = user.id

                
            if message.text == emoji.emojize(":red_heart:"):
                date = datetime.now().date()
                liked_user = Liked_Users.get((Liked_Users.user == lu) & (Liked_Users.liked_id == message.from_user.id))
                user = Users.get(Users.id == liked_user.user)
                me = Users.get(Users.id == message.from_user.id)

                liked_user = Liked_Users.create(user=me.id, liked_id=user.id, watched=False, mutually=True, date=date)
                liked_user.save()

                chat_id = message.from_user.id
                user_profile_link = f'Приятного общения с <a href="tg://openmessage?user_id={user.id}">@{user.name_tg}</a>!'
                await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")

                Liked_Users.delete().where((Liked_Users.user == user.id) & (Liked_Users.liked_id == me.id)).execute()
                step = "next_form"


            if step == "next_form":
                liked_user = Liked_Users.select().where(Liked_Users.liked_id == message.from_user.id).exists()
                if liked_user:
                    liked_user = Liked_Users.get(Liked_Users.liked_id == message.from_user.id)
                    user = Users.get(Users.id == liked_user.user)

                    photo = user.photo
                    input_file = InputFile(io.BytesIO(photo), filename="user_photo.jpg")
                    if user.information != None:
                        form = f"{user.name}, {user.age}"
                    else: 
                        form = f"{user.name}, {user.age}"
                    await bot.send_photo(chat_id=message.from_user.id, photo=input_file, caption=form)
                    if liked_user.message:
                        await message.answer(text=f"<b>Сообщение от пользователя:</b>\n\n{liked_user.message}", parse_mode="HTML")

                    lu = user.id


                    if liked_user.mutually == False:
                        l_d = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                        l_d.add(
                            KeyboardButton(text=emoji.emojize(":thumbs_down:")),
                            KeyboardButton(text=emoji.emojize(":red_heart:"))
                        )
                        await message.answer(text="Выбери действие:", reply_markup=l_d)
                    else:
                        chat_id = message.from_user.id
                        user_profile_link = f'Приятного общения с <a href="tg://openmessage?user_id={user.id}">@{user.name_tg}</a>!'
                        await bot.send_message(chat_id, text=user_profile_link, parse_mode="HTML")
                else:
                    await message.answer(text="У тебя больше нет уведомлений", reply_markup=types.ReplyKeyboardRemove())


if __name__ == "__main__":
    executor.start_polling(dp)