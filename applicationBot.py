import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, F
from datetime import datetime
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
dp = Dispatcher()
TOKEN = "7527530110:AAGbEpL--yYR-aVVe3ZKXOgDM3ZG-wQqGT0"
bot = Bot(token=TOKEN)
con = sqlite3.connect("applications.db")
db.pragma('journal_mode=WAL')
cur = con.cursor()

cur.execute(
    """CREATE TABLE IF NOT EXISTS Applications( ID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER,
    DateTime TEXT,
    Name TEXT,
    Contacts TEXT,
    Comments TEXT)
""")
cur.execute("""CREATE TABLE IF NOT EXISTS Admin(UserId INTEGER)""")

class Form(StatesGroup):
    waitingForName = State()
    waitingForContacts = State()
    waitingForComments = State()

btn1 = KeyboardButton(text = "Оставить заявку")
btn2 = KeyboardButton(text = "Помощь")
btn3 = KeyboardButton(text = "Просмотреть последнюю заявку")
btn4 = KeyboardButton(text = "Количество заявок")

keyboard1 = ReplyKeyboardMarkup(
    keyboard=[[btn1, btn2]],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие ниже:")

keyboard2 = ReplyKeyboardMarkup(
    keyboard=[[btn3, btn4]],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие ниже:")

def isAdmin(userId: int) -> bool:
    cur.execute("Select UserId FROM Admin LIMIT 1")
    row = cur.fetchone()
    return row is not None and row[0] == userId

@dp.message(CommandStart())
async def startHandler(message: Message, state: FSMContext) -> None:
    await state.clear()
    cur.execute("SELECT UserId FROM Admin")
    row = cur.fetchone()
    userid = row[0] if row else None
    
    if userid is None:
        cur.execute("INSERT INTO Admin VALUES(?)", (message.from_user.id,)) #надеемся что первый пользователь - админ
        con.commit()
        await message.answer("Здравствуйте! Вы админ, выберите действие.", reply_markup=keyboard2)
    elif userid == message.from_user.id:
        await message.answer("Здравствуйте! Вы админ, выберите действие.", reply_markup=keyboard2)
    else:
        await message.answer("Здравствуйте! Выберите действие.", reply_markup=keyboard1)

@dp.message(F.text.lower() == "просмотреть последнюю заявку")
async def showLast(message: Message) -> None:
    if not isAdmin(message.from_user.id):
        await message.answer("Это команда не доступна вам.")
        return
    cur.execute("SELECT * FROM Applications ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    lastApp = row if row else None
    if lastApp == None:
        await message.answer("Сейчас заявок нет.", reply_markup=keyboard2)
    else:
        await message.answer(f"ID заявки: {row['ID']}\nID пользователя: {row['UserID']}\nВремя написания заявки: {row['DateTime']}\nИмя: {row['Name']}\nКонтакты: [row['Contacts']}\nКомментарии: {row['Comments']}", reply_markup=keyboard2)

@dp.message(F.text.lower() == "количество заявок")
async def countApps(message: Message) -> None:
    if not isAdmin(message.from_user.id):
        await message.answer("Это команда не доступна вам.")
        return
    cur.execute("SELECT COUNT(*) FROM Applications")
    await message.answer(f"Сейчас {cur.fetchone()[0]} заявок.", reply_markup=keyboard2)

@dp.message(F.text.lower() == "помощь")
async def help(message: Message) -> None:
    await message.reply("Нажмите кнопку \"Оставить заявку\" и я вам помогу её отправить.")

@dp.message(F.text.lower() == "оставить заявку")
async def startWaiting(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.waitingForName)
    await message.reply("Напишите своё имя.")

@dp.message(Form.waitingForName)
async def processApplication(message: Message, state: FSMContext) -> None:
    data = await state.update_data(Name=message.text)
    await state.set_state(Form.waitingForContacts)
    await message.answer("Теперь напишите контактную информацию.")

@dp.message(Form.waitingForContacts)
async def processContacts(message: Message, state: FSMContext) -> None:
    data = await state.update_data(Contacts=message.text)
    await state.set_state(Form.waitingForComments)
    await message.answer("Теперь напишите комментарий.")

@dp.message(Form.waitingForComments)
async def processComments(message: Message, state: FSMContext) -> None:
    data = await state.update_data(Comments=message.text)
    await message.answer("Спасибо, ваша заявка сохранена.", reply_markup=keyboard1)

    data["UserID"] = message.from_user.id
    data["DateTime"] = datetime.now().strftime("%d %B %Y %H:%M:%S")
    cur.execute("INSERT INTO Applications(UserID, DateTime, Name, Contacts, Comments) VALUES(:UserID, :DateTime, :Name, :Contacts, :Comments)", data)
    con.commit()
    data = await state.get_data() 
    
    cur.execute("SELECT UserId FROM Admin")
    row = cur.fetchone()
    userid = row[0] if row else None
    if userid is not None:
        try: await bot.send_message(chat_id = userid, text = f"Оставили заявку.\nID заявки: {data['ID']}\nID пользователя: {data['UserID']}\nИмя: {data['Name']}\nКонтакты: [data['Contacts']}\nКомментарии: {data['Comments']}")
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")
    await state.clear()
    cur.close()
    

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
