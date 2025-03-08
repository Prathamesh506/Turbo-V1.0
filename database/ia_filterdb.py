import logging
from struct import pack
from bs4 import BeautifulSoup
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME
import regex 
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    
    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def save_file(media):
    """Save file in database"""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+|:)", " ", str(media.file_name))
    try:

        async def format_season_episode(html_caption,file_name = False):
            if html_caption:
                if not file_name:
                    # Convert HTML to plain text
                    soup = BeautifulSoup(html_caption, 'html.parser')
                    text_caption = soup.get_text()
                else:
                    text_caption = html_caption
                # Lowercase the text
                text_caption = text_caption.lower()

                # Remove emojis using regex module
                text_caption = regex.sub(r'\p{So}', '', text_caption)

                # Remove words starting with '@' and length less than or equal to 15
                text_caption = re.sub(r'@\w{1,20}\b', '', text_caption)

                # Remove URL links
                text_caption = re.sub(r'http[s]?://\S+', '', text_caption)

                # Remove Telegram links
                text_caption = re.sub(r'\bhttps?://t\.me/\S+\b', '', text_caption)

                # Remove links of the format https://t.me/joinchat/...
                text_caption = re.sub(r'https://t\.me/joinchat/\S+', '', text_caption)

                # Replace certain characters with spaces
                text_caption = re.sub(r"[.]", " ", text_caption)

                text_caption = re.sub(r'http\S+', '', text_caption)

                # Replace certain characters with spaces
                text_caption = re.sub(r"[@!$ _\-.+:*#⁓|\[\]]", " ", text_caption)

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

                words_to_remove = ["download", "team", "link","join","m2links","mkv","mkvcinemas","uploaded","Toonworld4all","Primefix","kayoanime","uploaded by","VegaMoviesX","cinearcade","cinehud"]

                # Create a regular expression pattern with all words to remove
                pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b'

                # Remove the specified words in a case-insensitive manner
                text_caption = re.sub(pattern, '', text_caption, flags=re.IGNORECASE)

                # Remove extra spaces between words
                text_caption = re.sub(r'\s+', ' ', text_caption)

                text_caption = text_caption.replace("हिंदी", "hindi").replace("తెలుగు", "telugu").replace("தமிழ்", "tamil").replace("ಕನ್ನಡ", "kannada").replace("മലയാളം", "malayalam")

                # Replace language abbreviations using a dictionary
                language_abbreviations = {"hin": "hindi", "eng": "english", "tam": "tamil", "tel": "telugu", "kan": "kannada", "mal": "malayalam", "mar": "marathi", "complete": "combined","2160p":"4k","completed":"combined","all episodes":"combined"}
                text_caption = re.sub(
                    r"\b(?:hin|eng|tam|tel|kan|mal|mar|complete|2160p|completed|all\s*episodes)\b",
                    lambda match: language_abbreviations.get(match.group(0), match.group(0)),
                    text_caption
                )

                text_caption = text_caption.title()
                # Convert back to HTML
                html_soup = BeautifulSoup(text_caption, 'html.parser')
                html_caption = str(html_soup)

                return html_caption
            else:
                return None

        # Assuming media.caption.html is your original HTML caption
        row_caption = media.caption.html if media.caption else None

        # Call the function with the HTML caption
        cleaned_caption = await format_season_episode(row_caption)
        if cleaned_caption is None:
            cleaned_caption = await format_season_episode(str(file_name),True)
            
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=cleaned_caption,
        )
        
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:      
            logger.warning(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database'
            )

            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

async def search_db(query, offset):
    offset = int(offset)
    max_results=10
    try:
        language_abbreviations = {"dual":"hindi english","multi":"hindi english tamil telugu"}
        query = re.sub(
        r"\b(?:dual|multi)\b",
        lambda match: language_abbreviations.get(match.group(0), match.group(0)),
        query)

        words = query.strip().split()

        regex_patterns = [fr"{re.escape(word)}" if word in ["sub", "rip"] else fr"\b{re.escape(word)}" for word in words]

        match_filters = [
            {"$match": {"caption": {"$regex": pattern, "$options": "i"}}} for pattern in regex_patterns
        ]
        sort_stage = {"$sort": {"created_at": -1}}  # Sorting by created_at field in descending order
        skip_stage = {"$skip": offset}
        limit_stage = {"$limit": max_results}

        pipeline = match_filters + [sort_stage, skip_stage, limit_stage]

        cursor = db[COLLECTION_NAME].aggregate(pipeline)

        result = []
        async for doc in cursor:
            media_instance = await Media.find_one(doc["_id"])
            result.append(media_instance)

        total_results = await db[COLLECTION_NAME].count_documents({"$and": [filter["$match"] for filter in match_filters]})
        if total_results <= 10:
            total_pages = 1
        else:
            remove = total_results%10
            total_pages = int((total_results-remove)/10)+1

        next_offset = offset + 10

        return result, next_offset, total_pages

    except Exception as e:
        logging.exception(f'ERROR: #SERACH DB\n{e}')
        return [], None, 0
