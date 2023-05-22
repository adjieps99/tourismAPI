# Model
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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



# Membaca data dari file CSV
data = pd.read_csv('tourist_spots.csv')

# Menginisialisasi TfidfVectorizer
tfidf = TfidfVectorizer()

# Mengubah kolom Review menjadi matriks TF-IDF
tfidf_matrix = tfidf.fit_transform(data['Review'])

# Menghitung kesamaan kosinus antara matriks TF-IDF
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Membuat fungsi untuk merekomendasikan tempat wisata
def recommend_places(name, cosine_sim=cosine_sim):
    # Mencari indeks dari tempat wisata yang sesuai dengan nama
    idx = data[data['Destination'] == name].index[0]

    # Mengurutkan skor kesamaan kosinus untuk tempat-tempat wisata lainnya
    sim_scores = list(enumerate(cosine_sim[idx]))

    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Mengambil 5 tempat wisata dengan skor kesamaan tertinggi (kecuali tempat input)
    top_scores = sim_scores[1:4]

    # Mengambil indeks tempat-tempat wisata yang direkomendasikan
    place_indices = [i[0] for i in top_scores]

    # Mengembalikan nama tempat-tempat wisata yang direkomendasikan
    return data['Destination'].iloc[place_indices]



@app.post("/recommendation", dependencies=[Depends(get_current_user)])
async def ktp_base64(info : Request):
    try: 
        req_info = await info.json()
        destination = req_info.get('destination')
        # print(destination)

        # ==================================================================
        # Contoh pemanggilan fungsi untuk merekomendasikan tempat wisata
        recommended_places = recommend_places(destination)
        # print(recommended_places)

        # Membuat list destination
        destination_list = []
        for i, place in enumerate(recommended_places):
            destination_list.append(place)

        # Membuat dictionary hasil
        result = {"status": True, "destination": destination_list}

        # Mengubah dictionary menjadi JSON
        json_output = json.dumps(result)

        # # Menampilkan output JSON
        # # print(json_output)
        # ==================================================================
        return  json.loads(json_output)
    except Exception:
        # print(e)
        ex = {"status": False,
              "message": "Location not found."}
        return JSONResponse(content=ex)