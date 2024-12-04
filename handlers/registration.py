from peewee import *
from aiogram import types


from keyboards import *
from database.models import *


async def us_name(message: types.Message): # name
    user = Users.delete().where(Users.id == message.from_user.id)
    user.execute()

    name = Users.create(id=int(message.from_user.id), name_tg=message.from_user.username, name=message.text)
    name.save()

    await message.answer(text=f"Сколько тебе лет?")


async def us_age(message: types.Message): # age
    Users.update(age=message.text).where(Users.id == int(message.from_user.id)).execute()
    await message.answer(text=f'Твой пол:', reply_markup=sex)


async def us_sex(message: types.Message, i): # sex
    if message.text.lower() == 'м' or message.text.lower() == 'm' or message.text == emoji.emojize(":man:"):
        Users.update(sex="М").where(Users.id == int(message.from_user.id)).execute()
        i+=1

    elif message.text.lower() == 'ж' or message.text == emoji.emojize(":woman:"):
        Users.update(sex="Ж").where(Users.id == int(message.from_user.id)).execute()
        i+=1

    else:
        await message.answer(text='Пол был введён неверно..\nПопробуй ещё раз:')

    if i == 1:
        skip = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        skip.add(KeyboardButton(text="Пропустить"))
        await message.answer(text=f"Напиши что-нибудь о себе", reply_markup=skip)
    return i


async def us_inf(message: types.Message, i): # information
    if message.text == "Пропустить":
        pass
    else: Users.update(information=message.text).where(Users.id == int(message.from_user.id)).execute()
    if i == 3:
        await message.answer(text="Вернуться к анкете..", reply_markup=my_profile)
    else:
        name = Users.get(Users.id == message.from_user.id)
        await message.answer(text=f'{name.name}, давай прикрепим твоё фото', reply_markup=types.ReplyKeyboardRemove())
    return i
            

async def ph(message: types.Message, photo, k):
    name = Users.update(photo=photo).where(Users.id == int(message.from_user.id)).execute()
    k = 0
    return k


async def ch_us_sex(message: types.Message, k): # user's sex
    sex = message.text
    sex_arr = ["Парни", "Девушки", "Всё равно", "м", "m", "ж"]
    k = 0
    for i in range(0, len(sex_arr)):
        if sex.lower() == sex_arr[i].lower():
            if i == 0 or i == 3 or i == 4:
                sex = "М"
            elif i == 1 or i == 5:
                sex = "Ж"
            elif i == 2:
                sex = "В"

            Users.update(fav_sex=sex).where(Users.id == message.from_user.id).execute()
            k = 1
            break
    if k == 0:
        await message.answer("Пол введён неверно. Повторите попытку.")
    return k