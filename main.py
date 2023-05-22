# Model
import csv
import json
import psycopg2
import numpy as np
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Fast API and JWT
import json
import jwt
from io import BytesIO
from fastapi.responses import JSONResponse,FileResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI,File, Depends, HTTPException, status, Request, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from tortoise import fields 
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model 
from pydantic import BaseModel


app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AUTHENTICATE

JWT_SECRET = 'myjwtsecret'

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)

User_Pydantic = pydantic_model_creator(User, name='User')
UserIn_Pydantic = pydantic_model_creator(User, name='UserIn', exclude_readonly=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)
    if not user:
        return False 
    if not user.verify_password(password):
        return False
    return user 

@app.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )

    user_obj = await User_Pydantic.from_tortoise_orm(user)

    token = jwt.encode(user_obj.dict(), JWT_SECRET)

    return {'access_token' : token, 'token_type' : 'bearer'}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )

    return await User_Pydantic.from_tortoise_orm(user)


@app.post('/users', response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic):
    user_obj = User(username=user.username, password_hash=bcrypt.hash(user.password_hash))
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)

@app.get('/users/me', response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    return user    

register_tortoise(
    app, 
    db_url='sqlite://db.sqlite3',
    modules={'models': ['main']},
    generate_schemas=True,
    add_exception_handlers=True
)

# =====================================================================================
# Load Data from ElephantSQL

# Membuat koneksi ke database
conn = psycopg2.connect(
    host="tiny.db.elephantsql.com",
    port="5432",
    database="kaufzser",
    user="kaufzser",
    password="Z3RIiZHbMzMk_7su0v6dGFm99bvOfkfU"
)

# Membuat kursor
cur = conn.cursor()

# Menjalankan pernyataan SQL untuk mengambil data
cur.execute("SELECT * FROM places")

# Mengambil semua baris hasil query
rows = cur.fetchall()

data = []
for item in rows:
    data.append([
        item[1],
        float(item[5]) if item[5] else 0.0,
        float(item[2]) if item[2] else 0.0,
        float(item[3]) if item[3] else 0.0,
        item[4],
        item[6]
    ])

# Menutup kursor dan koneksi
cur.close()
conn.close()
# =====================================================================================

# =====================================================================================
# Load Data from CSV

# data = []
# with open('exploreasy-dataset-ready.csv', 'r', newline='', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     for row in reader:
#         data.append([
#             row['name'],
#             float(row['rating']) if row['rating'] else 0.0,
#             float(row['latitude']) if row['latitude'] else 0.0,
#             float(row['longitude']) if row['longitude'] else 0.0,
#             row['address'],
#             row['review']
#         ])
# =====================================================================================

# Fungsi untuk menghitung jarak antara dua titik koordinat
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius bumi dalam kilometer

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2) * sin(dlat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) * sin(dlon/2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance


# Fungsi untuk menghitung rekomendasi destinasi
def get_recommendations(user_latitude, user_longitude, data):
    user_position = (user_latitude, user_longitude)

    # Menghitung jarak dari setiap destinasi ke posisi pengguna
    recommendation = []
    for item in data:
        item_lat = item[2]
        item_lon = item[3]
        item_position = (item_lat, item_lon)
        item_rating = float(item[1]) if item[1] else 0.0
        item_distance = calculate_distance(user_latitude, user_longitude, item_lat, item_lon)
        if  item_rating > 4.0 and item_distance <= 10.0:  # Filter rating > 4.0 dan jarak <= 10 km
            item.append(item_distance)
            recommendation.append(item)

    # Mengurutkan data berdasarkan jarak terdekat
    sorted_data = sorted(recommendation, key=lambda x: (x[5] is not None, x[5])) if recommendation else []


    return sorted_data[:3]  # Mengambil 3 destinasi terdekat

@app.post("/recommendation", dependencies=[Depends(get_current_user)])
async def tourist_recsys(info : Request):
    try: 
        req_info = await info.json()
        user_latitude = req_info.get('latitude')
        user_longitude = req_info.get('longitude')

        # ==================================================================
        recommendations = get_recommendations(user_latitude, user_longitude, data)

        # Menampilkan rekomendasi destinasi dalam format JSON
        result = []
        for dest in recommendations:
            result.append({
                'destination': dest[0],
                'rating': dest[1],
                'latitude': dest[2],
                'longitude': dest[3],
                'address': dest[4],
                'review': dest[5]
            })


        # # Mengurutkan data berdasarkan rating secara descending
        sorted_data = sorted(result, key=lambda x: x['rating'], reverse=True)

        # Mengonversi kembali menjadi JSON
        json_output = json.dumps(sorted_data, indent=4)
        # ==================================================================
        return  json.loads(json_output)
    except Exception:
        # print(e)
        ex = {"status": False,
              "message": "Location not found."}
        return JSONResponse(content=ex)