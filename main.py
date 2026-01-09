import asyncio
import json
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# --- НАСТРОЙКИ ---
API_TOKEN = '8467943750:AAHmF6BCHVO9K4CYaVAQfzEhva2l_tDCySE'
OWNER_ID = 8333520171  # Твой ID (Владелец)
ADMIN_CHAT_ID = -1003588542798  # ID группы модеров
MODS_FILE = 'mods.json'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Функции работы с базой модераторов
def load_mods():
    if os.path.exists(MODS_FILE):
        try:
            with open(MODS_FILE, 'r') as f:
                return json.load(f)
        except: return [OWNER_ID]
    return [OWNER_ID]

def save_mods(mods):
    with open(MODS_FILE, 'w') as f:
        json.dump(mods, f)

moderators = load_mods()

# --- БЛОК УПРАВЛЕНИЯ МОДЕРАТОРАМИ ---

@dp.message(Command("addmod"))
async def add_moderator(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    if message.reply_to_message:
        new_mod_id = message.reply_to_message.from_user.id
        if new_mod_id not in moderators:
            moderators.append(new_mod_id)
            save_mods(moderators)
            await message.reply(f"✅ ID {new_mod_id} назначен модератором.")
        else:
            await message.reply("Он уже модератор.")
    else:
        await message.reply("Ответь этой командой на сообщение будущего модератора.")

@dp.message(Command("delmod"))
async def delete_moderator(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    if message.reply_to_message:
        mod_id = message.reply_to_message.from_user.id
        if mod_id in moderators:
            if mod_id == OWNER_ID: return await message.reply("Себя нельзя уволить.")
            moderators.remove(mod_id)
            save_mods(moderators)
            await message.reply(f"❌ ID {mod_id} снят с поста.")
        else:
            await message.reply("Он не модератор.")

@dp.message(Command("modlist"))
async def list_mods(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    list_text = "👥 **Список модераторов:**\n" + "\n".join([f"• `{m}`" for m in moderators])
    await message.answer(list_text, parse_mode="Markdown")

# --- БЛОК ОБРАБОТКИ ЖАЛОБ ---

# Сообщения от пользователей (не из админ-чата)
@dp.message(F.chat.id != ADMIN_CHAT_ID)
async def forward_to_admins(message: types.Message):
    # Если пишет модер в личку боту — игнорим или даем инфу
    if message.from_user.id in moderators and message.chat.type == "private":
        return await message.answer("Вы модератор. Отвечайте на жалобы в группе.")

    # Инфо-сообщение для модеров (чтобы знать кому отвечать)
    user_info = f"📩 **Новая жалоба**\nОт: @{message.from_user.username or 'скрыто'}\nID: `{message.from_user.id}`"
    
    await bot.send_message(ADMIN_CHAT_ID, user_info, parse_mode="Markdown")
    await message.send_copy(chat_id=ADMIN_CHAT_ID)
    await message.answer("Ваша жалоба принята и передана модераторам.")

# Ответ модератора (Reply в админ-чате)
@dp.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
async def reply_handler(message: types.Message):
    # Проверка прав
    if message.from_user.id not in moderators:
        return # Просто игнорим сообщения от не-модеров

    # Ищем ID пользователя в истории переписки (в тексте выше)
    reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    user_id_match = re.search(r'ID: `(\d+)`', reply_text)

    if user_id_match:
        target_id = user_id_match.group(1)
        try:
            await bot.send_message(target_id, f"⚠️ **Ответ модератора:**\n\n{message.text}", parse_mode="Markdown")
            await message.reply("✅ Отправлено")
        except Exception as e:
            await message.reply(f"❌ Ошибка отправки: {e}")
    else:
        await message.reply("Не могу найти ID пользователя. Отвечайте именно на сообщение с текстом 'ID: ...'")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
          
