from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from info import LOG_CHANNEL,MYCHANNEL,DLT
from database.users_chats_db import db
from utils import temp
from Script import script
import asyncio 
import random


@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        if not await db.get_chat(message.chat.id):
            total=await bot.get_chat_members_count(message.chat.id)
            r_j = message.from_user.mention if message.from_user else "Anonymous" 
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, r_j))       
            await db.add_chat(message.chat.id, message.chat.title)
        
        buttons = [
                    InlineKeyboardButton('My Channel', url=f"https://t.me/{MYCHANNEL}")
                 ]
        reply_markup=InlineKeyboardMarkup(buttons)
        addmsg = await message.reply_text(
            text=f"<b>Thankyou For Adding Me In {message.chat.title} ❣️\n\nIf you have any questions & doubts about using me contact my Channel.</b>",
            reply_markup=reply_markup)
        await asyncio.sleep(600)
        await addmsg.delete(DLT)
        
    else:
        return
