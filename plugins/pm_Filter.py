import re
import ast
import math
import imdb
import html
import imdb
import regex
import asyncio
import logging
import pyrogram

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import MessageNotModified
from Script import script

from utils import get_size, is_subscribed, temp
from info import ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, DLT
from database.users_chats_db import db
from database.watch import search_movie_db
from database.ia_filterdb import get_file_details,search_db

lock = asyncio.Lock()
ia = imdb.IMDb()

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}

@Client.on_message((filters.group | filters.private) & filters.text & filters.incoming)
async def auto_filter(client, msg):

    if msg.text is None or msg.text.startswith(("/", "#")) or is_invalid_message(msg) or contains_url(msg.text):
        await msg.delete()
        return

    ptext = await process_text(msg.text)
    search_details, search = detail_extraction(ptext, type=True)
    files = []

    
    files, offset, total_pages = await search_db(search.lower(), offset=0)
    if files:
        await db.store_search(msg.from_user.id, search)

    else:     
        as_msg = await msg.reply_text("<b>initiating..</b>")
        await asyncio.sleep(0.3)
        as_msg = await as_msg.edit_text("<b>Rapid AutoCorrect⚡</b>")

        temp_detail = search_details.copy()

        temp_detail['title'] = await search_movie_db(temp_detail['title'].lower())
        if temp_detail['title'] is not None:
            temp_search = str_to_string(temp_detail)
            files, offset, total_pages = await search_db(temp_search.lower(), offset=0)
            if files:
                search = temp_search
                await db.store_search(msg.from_user.id, search)
        await as_msg.delete()
                    

    if files:
        btn = await result_btn(files, msg.from_user.id, search)
        btn = await navigation_buttons(btn, msg, total_pages, offset)
        cap = f"<b>Hey {msg.from_user.mention},\n\nFᴏᴜɴᴅ Rᴇꜱᴜʟᴛꜱ Fᴏʀ Yᴏᴜʀ\nSearch:</b> {search.title()}"
        result_msg = await msg.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))

    if not files:
        cap = """<i><b>This Movie Not Found in Database\n\nPlease Check Your Spelling On Google & Try Again ✅</b></i>"""
        
        # btn = [
        # [
        #     InlineKeyboardButton("Request The Movie 📬", url = "https://t.me/+kBTn6LN3n9Y3MGM9"),
        # ]]
        result_msg = await msg.reply_text(cap)
        await asyncio.sleep(120)
        await result_msg.delete()
        await msg.delete()
        return
    try:
        await asyncio.sleep(DLT)
        await result_msg.delete()
        await msg.delete()
    except: pass

#BUTTONS
async def result_btn(files, user_id, search):
    btn = [
        [
            InlineKeyboardButton(
                text=f"[{get_size(file.file_size)}] {html.unescape(file.caption[:45].strip())}",
                url=f"https://telegram.dog/{temp.U_NAME}?start=CodeiBots_{file.file_id}"
            ),
        ]        
        for file in files
    ]

    common_btns = [
        [
            InlineKeyboardButton("Lᴀɴɢᴜᴀɢᴇ", callback_data=f"select_language#{user_id}"),
            InlineKeyboardButton("Qᴜᴀʟɪᴛʏ", callback_data=f"select_quality#{user_id}"),
            InlineKeyboardButton("Sᴇᴀꜱᴏɴ", callback_data=f"select_season#{user_id}")
        ]
    ]
    btn = common_btns + btn    
    return btn

async def navigation_buttons(btn,message, total_pages, offset):#navigation btns
    req = message.from_user.id if message.from_user else 0
    offset = int(offset)
    offsetpageno = int(math.ceil(int(offset)/10))
    if total_pages == 1 :
        btn.append([
            InlineKeyboardButton(text=f" 1 / 1 ",callback_data="callback_none")]
        )
    elif offsetpageno == total_pages :
        btn.append([
            InlineKeyboardButton(text="⏪ Back",callback_data=f"next_{req}_{offset-20}"),
            InlineKeyboardButton(text=f" {offsetpageno} / {total_pages}",callback_data="callback_none")]
        )
    elif offset == 10 :
        btn.append([
            InlineKeyboardButton(text=f" 1 / {total_pages}",callback_data="callback_none"),
            InlineKeyboardButton(text="Next ⏩ ",callback_data=f"next_{req}_{offset}")]
        )
    else:
        btn.append([
            InlineKeyboardButton(text="⏪ Back",callback_data=f"next_{req}_{offset-20}"),
            InlineKeyboardButton(text=f"{offsetpageno} / {total_pages}",callback_data="callback_none"),
            InlineKeyboardButton(text="Next ⏩",callback_data=f"next_{req}_{offset}") ]
        )  
    return btn

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        _, req, offset = query.data.split("_")
        offset = int(offset)
        req = int(req)
    except ValueError:
        logger.exception('ERROR: #NEXT BUTTON')
        return 

    search = await db.retrieve_latest_search(query.from_user.id)

    if req != query.from_user.id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    try:
        offset = int(offset)
    except ValueError:
        offset = 0

    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return

    files, n_offset, total_pages = await search_db(search, offset)

    if not files:
        return

    btn = await result_btn(files, req, search)
    query.text = search
    btn = await navigation_buttons(btn, query, total_pages, n_offset)
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
    except pyrogram.errors.exceptions.flood_420.FloodWait as e:
        await query.answer("Flood Wait 15s ⌛")
    except pyrogram.errors.exceptions.bad_request_400.QueryIdInvalid as e:
        logger.error("Query ID is invalid or expired.")
        return  # Don't proceed further if the query ID is invalid
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^select_lang"))
async def select_language(bot, query):
    _, userid= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("⇃  ᴄʜᴏᴏsᴇ ʟᴀɴɢᴜᴀɢᴇ  ⇂", callback_data=f"callback_none")
    ],[
        InlineKeyboardButton("Eɴɢʟɪꜱʜ", callback_data=f"add_filter#{userid}#english"),
        InlineKeyboardButton("Hɪɴᴅɪ", callback_data=f"add_filter#{userid}#hindi")
    ],[
        InlineKeyboardButton("Tᴀᴍɪʟ", callback_data=f"add_filter#{userid}#tamil"),
        InlineKeyboardButton("Tᴇʟᴜɢᴜ", callback_data=f"add_filter#{userid}#telugu")
    ],[
        InlineKeyboardButton("Mᴀʀᴀᴛʜɪ", callback_data=f"add_filter#{userid}#mar"),
        InlineKeyboardButton("Mᴀʟᴀʏᴀʟᴀᴍ", callback_data=f"add_filter#{userid}#mal")
    ],[
        InlineKeyboardButton("Kᴀɴɴᴀᴅᴀ", callback_data=f"add_filter#{userid}#kan"),
        InlineKeyboardButton("Dᴜᴀʟ Aᴜᴅɪᴏ", callback_data=f"add_filter#{userid}#dual")
    ],[
        InlineKeyboardButton("Mᴜʟᴛɪ Aᴜᴅɪᴏ", callback_data=f"add_filter#{userid}#multi"),
        InlineKeyboardButton("ꜱᴜʙᴛɪᴛʟᴇꜱ", callback_data=f"add_filter#{userid}#sub")
    ],[
        InlineKeyboardButton("Cʟᴇᴀʀ", callback_data=f"add_filter#{userid}#clearlanguage"),
        InlineKeyboardButton("Bᴀᴄᴋ", callback_data=f"add_filter#{userid}#mainpage")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^select_lang"))
async def select_language(bot, query):
    _, userid= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("⇃  ᴄʜᴏᴏsᴇ ʟᴀɴɢᴜᴀɢᴇ  ⇂", callback_data=f"callback_none")
    ],[
        InlineKeyboardButton("Eɴɢʟɪꜱʜ", callback_data=f"add_filter#{userid}#english"),
        InlineKeyboardButton("Hɪɴᴅɪ", callback_data=f"add_filter#{userid}#hindi")
    ],[
        InlineKeyboardButton("Tᴀᴍɪʟ", callback_data=f"add_filter#{userid}#tamil"),
        InlineKeyboardButton("Tᴇʟᴜɢᴜ", callback_data=f"add_filter#{userid}#telugu")
    ],[
        InlineKeyboardButton("Mᴀʀᴀᴛʜɪ", callback_data=f"add_filter#{userid}#mar"),
        InlineKeyboardButton("Mᴀʟᴀʏᴀʟᴀᴍ", callback_data=f"add_filter#{userid}#mal")
    ],[
        InlineKeyboardButton("Kᴀɴɴᴀᴅᴀ", callback_data=f"add_filter#{userid}#kan"),
        InlineKeyboardButton("Dᴜᴀʟ Aᴜᴅɪᴏ", callback_data=f"add_filter#{userid}#dual")
    ],[
        InlineKeyboardButton("Mᴜʟᴛɪ Aᴜᴅɪᴏ", callback_data=f"add_filter#{userid}#multi"),
        InlineKeyboardButton("ꜱᴜʙᴛɪᴛʟᴇꜱ", callback_data=f"add_filter#{userid}#sub")
    ],[
        InlineKeyboardButton("Cʟᴇᴀʀ", callback_data=f"add_filter#{userid}#clearlanguage"),
        InlineKeyboardButton("Bᴀᴄᴋ", callback_data=f"add_filter#{userid}#mainpage")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^select_quality"))
async def select_quality(bot, query):
    _, userid= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("⇃  ᴄʜᴏᴏsᴇ ϙᴜᴀʟɪᴛʏ  ⇂", callback_data=f"callback_none")
    ],[
        InlineKeyboardButton("HD/Rips", callback_data=f"add_filter#{userid}#rip"),
        InlineKeyboardButton("360P", callback_data=f"add_filter#{userid}#360p")
    ],[
        InlineKeyboardButton("480P", callback_data=f"add_filter#{userid}#480p"),
        InlineKeyboardButton("720P", callback_data=f"add_filter#{userid}#720p")
    ],[
        InlineKeyboardButton("1080P", callback_data=f"add_filter#{userid}#1080p"),
        InlineKeyboardButton("4K", callback_data=f"add_filter#{userid}#4k")
    ],[
        InlineKeyboardButton("Clear", callback_data=f"add_filter#{userid}#clearquality"),
        InlineKeyboardButton("Back", callback_data=f"add_filter#{userid}#mainpage")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^select_season"))
async def select_season(bot, query):
    _, userid= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("⇃  ᴄʜᴏᴏsᴇ ꜱᴇᴀꜱᴏɴ  ⇂", callback_data=f"callback_none")
    ],[
        InlineKeyboardButton("Season 01", callback_data=f"add_filter#{userid}#s01"),
        InlineKeyboardButton("Season 02", callback_data=f"add_filter#{userid}#s02")
    ],[
        InlineKeyboardButton("Season 03", callback_data=f"add_filter#{userid}#s03"), 
        InlineKeyboardButton("Season 04", callback_data=f"add_filter#{userid}#s04")
    ],[
        InlineKeyboardButton("Season 05", callback_data=f"add_filter#{userid}#s05"),
        InlineKeyboardButton("Season 06", callback_data=f"add_filter#{userid}#s06")
    ],[
        InlineKeyboardButton("Season 07", callback_data=f"add_filter#{userid}#s07"), 
        InlineKeyboardButton("Season 08", callback_data=f"add_filter#{userid}#s08")
    ],[
        InlineKeyboardButton("Season 09", callback_data=f"add_filter#{userid}#s09"),
        InlineKeyboardButton("Season 10", callback_data=f"add_filter#{userid}#s10")
    ],[
        InlineKeyboardButton("Season 11", callback_data=f"add_filter#{userid}#s11"), 
        InlineKeyboardButton("Season 12", callback_data=f"add_filter#{userid}#s12")
    ],[
        InlineKeyboardButton("Clear", callback_data=f"add_filter#{userid}#clearseason"),
        InlineKeyboardButton("Back", callback_data=f"add_filter#{userid}#mainpage")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^add_filter"))
async def filtering_results(bot, query): 
    user_id = query.from_user.id
    data_parts = query.data.split("#")

    if len(data_parts) == 4: #IMDB RESULT
        _, userid, the_filter, search = data_parts
        search = await process_text(search)
    else:
        _, userid, the_filter = data_parts
        if the_filter == "imdbclse":
            await query.answer(f"🤖 Closing IMDb Results")
            await query.message.delete()
            
        search = await db.retrieve_latest_search(user_id)

    if int(userid) != user_id:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    
    if the_filter in ["clearlanguage", "clearquality", "clearseason"]:
        search = clear_filter(search, the_filter)
    elif the_filter != "mainpage":
        search = f"{search} {the_filter}"
        details, search = detail_extraction(search)

    files, offset, total_pages = await search_db(search, offset=0)

    query.text = search
    if files:
        await db.store_search(user_id, search)
        btn = await result_btn(files, user_id,search)
        btn = await navigation_buttons(btn, query, total_pages, offset)
        try:
            cap = f"<b>Hey {query.from_user.mention},\n\nFᴏᴜɴᴅ Rᴇꜱᴜʟᴛꜱ Fᴏʀ Yᴏᴜʀ\nSearch: </b>{search.title()}"
            if len(data_parts) == 4:
                await query.answer(f"🤖 Fetching Results")
                await query.message.delete()
                result_msg = await query.message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
                await asyncio.sleep(DLT)
                await result_msg.delete()
            else:
                await query.edit_message_text(
                    text=cap,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                if the_filter in ["clearlanguage", "clearquality", "clearseason"]:
                    await query.answer(f"🤖 Removed {the_filter[5:].title()} Filter")
                elif the_filter != "mainpage":
                    await query.answer(f"🤖 Results For : {the_filter.title()}")
        except MessageNotModified:
            pass
    else:
        return await query.answer(f"ꜱᴏʀʀʏ, ɴᴏ ғɪʟᴇꜱ ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ ғᴏʀ ʏᴏᴜʀ ϙᴜᴇʀʏ 🔍", show_alert=True)


#UTILITY
async def process_text(text_caption): #text is filter and processed
    text_caption = text_caption.lower()

    # Remove emojis using regex module
    text_caption = regex.sub(r'\p{So}', '', text_caption)

    # Replace certain characters with spaces
    text_caption = re.sub(r"[@!$ _\-.+:*#⁓(),/?]", " ", text_caption)

    # Replace language abbreviations using a dictionary
    language_abbreviations = {"session":"season","hin": "hindi", "eng": "english", "tam": "tamil", "tel": "telugu","wanda vision":"wandavision","salar":"salaar","spiderman":"spider man","spiderverse":"spider verse","complete":"combined","12 th":"12th","completed":"combined","all episodes":"combined","all episode":"combined"}
    text_caption = re.sub(
        r"\b(?:session|hin|eng|tam|tel|wanda\s*vision|salar|spiderman|spiderverse|complete|12\s*th|completed|all\s*episodes|all\s*episode)\b",
        lambda match: language_abbreviations.get(match.group(0), match.group(0)),
        text_caption
    )

    # Insert space between 's' and 'e' in patterns like 's01e04'
    text_caption = re.sub(r's(\d+)e(\d+)', r's\1 e\2', text_caption, flags=re.IGNORECASE)

    # Insert space between 's' and 'e' in patterns like 's1e4'
    text_caption = re.sub(r's(\d+)e', r's\1 e', text_caption, flags=re.IGNORECASE)

    # Convert 'ep' followed by a number to 'e' followed by that number with leading zeros
    text_caption = re.sub(r'\bep(\d+)\b', r'e\1', text_caption, flags=re.IGNORECASE)
    text_caption = re.sub(r'\bep (\d)\b', r'e0\1', text_caption, flags=re.IGNORECASE)
    text_caption = re.sub(r'\bep (\d{2,})\b', r'e\1', text_caption, flags=re.IGNORECASE)

        # Convert single-digit 'e' to two-digit 'e'
    text_caption = re.sub(r'\be(\d)\b', r'e0\1', text_caption, flags=re.IGNORECASE)

    # Convert single-digit 's' to two-digit 's'
    text_caption = re.sub(r'\bs(\d)\b', r's0\1', text_caption, flags=re.IGNORECASE)

    # Formatting for season and episode numbers (padding with zeros)
    text_caption = re.sub(r'\bseason (\d+)\b', lambda x: f's{x.group(1).zfill(2)}', text_caption, flags=re.IGNORECASE)
    text_caption = re.sub(r'\bepisode (\d+)\b', lambda x: f'e{x.group(1).zfill(2)}', text_caption, flags=re.IGNORECASE)

    #testing
    text_caption = ' '.join(['e' + word[2:] if word.startswith('e0') and word[2:].isdigit() and len(word) >= 4 else word for word in text_caption.split()])

    words_to_remove = ["full","video","videos","movie", "movies","series","dubbed","send","file","audio","to","language","quality","qua","aud","give","files","hd","in","dub","review"]

    # Create a regular expression pattern with all words to remove
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b'

    # Remove the specified words in a case-insensitive manner
    text_caption = re.sub(pattern, '', text_caption, flags=re.IGNORECASE)

    # Remove extra spaces between words
    text_caption = re.sub(r'\s+', ' ', text_caption)
    
    return text_caption

def detail_extraction(text,type=False): #extractes details title ans all

    languages = ["english", "hindi", "tamil", "telugu", "kannada", "malayalam", "marathi", "multi", "dual","kan","mal","mar"]
    qualities = ["720p", "1080p", "480p", "4k", "360p","rip","hd"]
    subs = ["sub", "esub", "msub", "esubs", "msubs"]
    extra_words = ["combined"]

    # Define patterns for 's01', 'e01', 'part 1', and a four-digit number (year)
    season_pattern = re.compile(r'\bs\d+', re.IGNORECASE)
    episode_pattern = re.compile(r'\be\d+', re.IGNORECASE)
    # part_pattern = re.compile(r'part\s*(\d+)', re.IGNORECASE)
    year_pattern = re.compile(r'\b\d{4}\b')

    details = {
        'title': text,
        'year': None,
        'season': None,
        'episode': None,
        'language': None,
        'quality': None,
        'sub': None,
        'comb':None
    }

    # Extract patterns for language
    if type:
        found_languages = []
        for word in text.split():
            if word in languages:
                found_languages.append(word)

        if found_languages:
            details['language'] = ' '.join(found_languages)
        else:
            details['language'] = None
            
    else: #only one lang
        for word in text.split():
            for lang in languages:
                if lang == word:
                    details['language'] = lang

    # Extract patterns for quality
    for word in text.split():
        for quality in qualities:
            if quality == word:
                details['quality'] = quality

    # Extract patterns for subtitles
    for word in text.split():
        for sub in subs:
            if sub == word:
                details['sub'] = sub

    # Extract pattern for year
    match_year = year_pattern.search(text)
    if match_year:
        details['year'] = match_year.group()
        details['title'] = re.sub(year_pattern, '', details['title']).strip()

    # Extract patterns for season
    match_season = season_pattern.findall(text)
    if match_season:
        details['season'] = match_season[-1]
        details['title'] = re.sub(season_pattern, '', details['title']).strip()

    # Extract patterns for episode
    match_episode = episode_pattern.findall(text)
    if match_episode:
        details['episode'] = match_episode[-1]
        details['title'] = re.sub(episode_pattern, '', details['title']).strip()

     # Extract 'combined'
    details['comb'] = "combined" if "combined" in text.lower() else None

    # Remove all qualities, subtitles, year, and other languages from the title
    for term in qualities + subs + languages + extra_words:
        matches = re.findall(r'\b(?:{})\b'.format(term), details['title'])
        if matches:
            details['title'] = re.sub(r'\b(?:{})\b'.format(term), '', details['title']).strip()
    formatted_info = ' '.join(str(value) for value in details.values() if value is not None)
    formatted_info = formatted_info.replace("'", '').replace('{', '').replace('}', '')
    # Remove extra spaces between words
    formatted_info = re.sub(r'\s+', ' ', formatted_info)
    return details , formatted_info

def is_invalid_message(msg):  # Checks if the message is invalid
    if len(msg.text) < 2 or re.match(r'^\s*$', msg.text) or \
            re.findall(r"((^/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", msg.text) or \
            len(msg.text) > 100:
        return True
    return False

async def no_resultx(msg,text="<i>No Results Found Please Provide Correct Title!</i>"):#no result message
    k = await msg.reply_text(f"{text}")
    await asyncio.sleep(7)
    await k.delete()
    return

def clear_filter(search, the_filter): #function clear a type of filter
    deatails, search = detail_extraction(search)
    
    if the_filter == "clearlanguage":
        deatails['language'] = None
        deatails['sub'] = None
    elif the_filter == "clearquality":
        deatails['quality'] = None
    elif the_filter == "clearseason":
        deatails['season'] = None

    search = str_to_string(deatails)
    return search

def str_to_string(details): #converts from structure deatils to string
    formatted_info = ' '.join(str(value) for value in details.values() if value is not None)
    formatted_info = formatted_info.replace("'", '').replace('{', '').replace('}', '')
    return formatted_info

def contains_url(message):
    url_pattern = re.compile(r'https?://\S+')
    match = re.search(url_pattern, message)
    return bool(match)

def extract_season(text):
    season_pattern = re.compile(r'\bs(\d+)', re.IGNORECASE)
    
    match_season = season_pattern.search(text)
    
    if match_season:
        return match_season.group(1)
    else:
        return None
    
#CALLBACKS 
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    
    if query.data == "callback_none":
        await query.answer() 

    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Tʜᴀᴛ's ɴᴏᴛ ғᴏʀ ʏᴏᴜ!!", show_alert=True)

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await None, None, None, None
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("First Join My Channel", show_alert=True)
            return
        
        await query.message.delete()

        ident, file_id = query.data.split("#")

        
        files_ = await get_file_details(file_id)

        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=False,
        )
