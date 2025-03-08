from info import  DATABASE_NAME
DATABASE_URI = "mongodb+srv://MovieNames:MovieNames@cluster0.8rwer.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
from motor.motor_asyncio import AsyncIOMotorClient
from fuzzywuzzy import fuzz
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

async def search_movie_db(title_query):
    best_match = None
    best_score = 0
    async for movie in db.movies.find({}, {"title": 1}):
        movie_title = movie['title']
        score = fuzz.ratio(title_query, movie_title)
        if score > 80 and score > best_score:
            best_match = movie_title
            best_score = score
    return best_match
    
