import re
from os import environ
from Script import script 

id_pattern = re.compile(r'^.\d+$')

##### >> TURBO ⚡ LIGHT SPEED

BOT_TOKEN = environ.get("BOT_TOKEN", "7774366144:AAGUTKCnRaVoSSYPZd6AGebZcJrvzNH-v5o")
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://iMovies99:iMovies99@cluster0.nh872.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

SESSION = environ.get('SESSION', 'iSession99')
API_ID = "3704207"
API_HASH = environ.get("API_HASH", "8d20e46f5413139329f2ec753f7c482a")
AUTH_CHANNEL = int(-1001575554437)
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1531899507').split()]
MYCHANNEL = "iMovies99"
MYGROUP = "+xYHRwJA21io2ZmY9"

AUTH_USERS = ("1531899507")


### >> DATABASE CHANNELS
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1001997311406 -1001908988097 -1001977939308 -1002052107035 -1002031777198 -1002120266966 -1001638006524').split()]

DATABASE_NAME = environ.get('DATABASE_NAME', "Cluster0")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Bot_DataBase')
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002131280557'))

DLT = int(environ.get('DLT', 300))
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
PORT = environ.get("PORT", "8080")

#---------------------------- LOGS -----------------------------------



LOG_STR = "Current Cusomized Configurations are:-\n"
LOG_STR += (f"CUSTOM_FILE_CAPTION enabled with value {CUSTOM_FILE_CAPTION}, your files will be send along with this customized caption.\n" if CUSTOM_FILE_CAPTION else "No CUSTOM_FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += (f"MAX_LIST_ELM Found, long list will be shortened to first {MAX_LIST_ELM} elements\n" if MAX_LIST_ELM else "Full List of casts and crew will be shown in imdb template, restrict them by adding a value to MAX_LIST_ELM\n")

