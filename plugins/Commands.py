import os
import sys
import psutil
import base64
import logging
import asyncio
from Script import script
from datetime import datetime,timedelta
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import Media, get_file_details
from database.users_chats_db import db
from info import  ADMINS,AUTH_CHANNEL, LOG_CHANNEL, CUSTOM_FILE_CAPTION,MYCHANNEL,DLT,MYGROUP
from utils import  get_size, is_subscribed, temp


logger = logging.getLogger(__name__)
BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):    

    #IF NEW GROUP
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        alive = await message.reply_text("...")
        await asyncio.sleep(2)
        await alive.delete()
        try: 
            await message.delete()
        except: pass
        return
    
    #NEW USER
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))

    #Only Start
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('〆   Add Me To Your Group   〆', url=f"http://t.me/{temp.U_NAME}?startgroup=true")
            ],[
                    InlineKeyboardButton('My Channel', url = f"https://t.me/{MYCHANNEL}"),
                    InlineKeyboardButton('My Group', url = f"https://t.me/{MYGROUP}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        start_response = await message.reply_text(f"<i>Searching for Movie ?</i>")
        await asyncio.sleep(0.4)
        start_response = await start_response.edit_text("<i>Just Name it ⚡ </i>")
        await asyncio.sleep(0.3)
        start_response = await start_response.edit_text("✨")
        await asyncio.sleep(0.2)

        await start_response.edit_text(
            text=script.START_TXT.format(message.from_user.mention, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await asyncio.sleep(DLT)
        await start_response.delete()
        await message.delete()
        return
    
    #force Sub
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make Sure i'm in Force Sub Channel.")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "Join My Channel", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton("Try Again", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton("Try Again", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text=f"<b>Hey {message.from_user.mention},\n\nPlease Join My Channel To Use Me!</b>\nonce you are joined click on try again you will get files.",
            reply_markup=InlineKeyboardMarkup(btn)
            )
        return
    
    #other ultility cmds
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('〆   Add Me To Your Group   〆', url=f"http://t.me/{temp.U_NAME}?startgroup=true")
            ],[
                    InlineKeyboardButton('My Channel', url = f"https://t.me/{MYCHANNEL}"),
                    InlineKeyboardButton('My Group', url = f"https://t.me/{MYGROUP}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        start_response = await message.reply_text(f"<i>Searching for Movie ?</i>")
        await asyncio.sleep(0.4)
        start_response = await start_response.edit_text("<i>Just Name it ⚡ </i>")
        await asyncio.sleep(0.3)
        start_response = await start_response.edit_text("✨")
        await asyncio.sleep(0.2)

        await start_response.edit_text(
            text=script.START_TXT.format(message.from_user.mention, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await asyncio.sleep(DLT)
        await start_response.delete()
        await message.delete()
        return
    
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
        
    files_ = await get_file_details(file_id)           
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        except:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("utf-8")).split("_", 1)

        try:      
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('❌ No such file exists.')
    
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption

    if f_caption is None:
        f_caption = f"{files.file_name}"
    
    await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False
    )
  
@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('Logs.txt')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('stats') & filters.user(ADMINS))
async def get_ststs(bot, message):
    Stats_msg = await message.reply('Fetching stats..')
    total_users = await db.total_users_count()
    totl_chats = await db.total_chat_count()
    files = await Media.count_documents()
    size = await db.get_db_size()
    free = 536870912 - size
    size = get_size(size)
    free = get_size(free)
    await Stats_msg.edit(script.STATUS_TXT.format(files, total_users, totl_chats, size, free))

#RESTART 
@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    msg = await bot.send_message(text="**Rebooting**", chat_id=message.chat.id)       
    await asyncio.sleep(3)
    await msg.edit("**𝙱ot Restarted ✅ **")
    os.execl(sys.executable, sys.executable, *sys.argv)

#DELETE ALL FILES
@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all the indexed files from database, Continue ?',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Yes", callback_data="autofilter_delete_all"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Cancle", callback_data=f"close_data#{message.from_user.id}"
                    )
                ],
            ]
        ),
        quote=True,
    )
       
#SYSTEM RESOURCES STATUS
@Client.on_message(filters.command('rstats') & filters.user(ADMINS))
async def get_system_info(bot, message):
    rju = await message.reply('Fetching stats..')
    cpu_percent = psutil.cpu_percent()
    ram_percent = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/')
    disk_usage_percent = disk_usage.percent
    disk_free_gb = round(disk_usage.free / (1024**3), 2)
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    uptime_str = str(timedelta(seconds=uptime.total_seconds()))
    uptime_str = uptime_str.split('.')[0]
    status_message = script.SYS_STATUS_TXT.format(cpu_percent, ram_percent, disk_usage_percent, disk_free_gb, uptime_str)
    await rju.edit(status_message)
