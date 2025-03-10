import motor.motor_asyncio
from info import DATABASE_NAME , DATABASE_URI
from datetime import datetime
import pymongo
import pytz

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.verif_col = self.db.verification_counts
        self.timezone = pytz.timezone('Asia/Kolkata') 
        self.col = self.db.users
        self.grp = self.db.groups
        self.search_col = self.db.search_data
        try:
            self.search_col.drop_index("timestamp_1")
        except pymongo.errors.OperationFailure as e:
            print(f"Error dropping index 'timestamp_1'")
        try:
            self.search_col.create_index("timestamp", expireAfterSeconds=6000)
        except pymongo.errors.OperationFailure as e:
            print(f"Error creating index 'timestamp': {e}")

    async def store_search(self, user_id, search_query):
        search_data = {
            'user_id': user_id,
            'search_query': search_query,
            'timestamp': datetime.utcnow()
        }
        await self.search_col.insert_one(search_data)

    async def retrieve_latest_search(self, user_id):
        result = await self.search_col.find_one({'user_id': user_id}, sort=[('timestamp', pymongo.DESCENDING)])
        latest_search = result.get('search_query') if result else None
        return latest_search

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )

    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
        )
 
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    
    async def get_username_by_id(self, user_id):
        user = await self.col.find_one({'id': int(user_id)})
        return user.get('name') if user else None

    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)
    
    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')

    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    
    async def get_all_chats(self):
        return self.grp.find({})

    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']


db = Database(DATABASE_URI, DATABASE_NAME)