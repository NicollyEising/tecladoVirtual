import hashlib
import base64
import random
import secrets
from datetime import datetime, timedelta
from grpc import StatusCode
from pymongo import MongoClient
from cryptography.fernet import Fernet
import os
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
from passlib.context import CryptContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import time

MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]
users_collection = db["users"]

FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)
SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  
MAX_SESSIONS_BEFORE_REUSE = 1000  
app = FastAPI()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_EXPIRATION_MINUTES = 15 

def generate_random_pairs():
    numbers = list(range(1, 10)) 
    random.shuffle(numbers)
    return [[numbers[i], numbers[i + 1]] for i in range(0, len(numbers) - 1, 2)]

def generate_random_numbers():
    return [random.randint(0, 9) for _ in range(10)]  

def map_digit_to_button(digit, pairs):
    """
    Mapeia um dígito para o botão correspondente (par de números).
    Retorna o primeiro número do par que contém o dígito.
    """
    for pair in pairs:
        if digit in pair:
            return pair[0] 
    raise ValueError(f"Dígito {digit} não encontrado em nenhum botão.")

def transform_password(password, pairs):
    """
    Transforma a senha original em uma sequência de botões.
    Exemplo: "12345" → "112233" com pares [1,2], [3,4], [5,6].
    """
    transformed = ""
    for digit in password:
        button_number = map_digit_to_button(int(digit), pairs)
        transformed += str(button_number) * 2 
    return transformed

def hash_session_id(session_id):
    return base64.urlsafe_b64encode(hashlib.sha256(session_id.encode()).digest()).decode()

def save_session(hashed_id, sequence, expiration_time, attempts=0, ip_address=None):
    session_data = {
        "session_id": hashed_id,
        "sequence": sequence,
        "expires_at": expiration_time,
        "attempts": attempts,
        "ip_address": ip_address
    }
    sessions_collection.update_one({"session_id": hashed_id}, {"$set": session_data}, upsert=True)

class User(BaseModel):
    username: str
    password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_session(hashed_id):
    return sessions_collection.find_one({"session_id": hashed_id})

def delete_session(hashed_id):
    result = sessions_collection.delete_one({"session_id": hashed_id})
    return result.deleted_count > 0

def get_session_count():
    return sessions_collection.count_documents({})

def is_ip_blocked(ip_address):
    blocked_ip = blocked_ips_collection.find_one({"ip": ip_address})
    if blocked_ip and blocked_ip["expires_at"] > datetime.utcnow():
        return True
    return False

def block_ip(ip_address):
    expires_at = datetime.utcnow() + timedelta(seconds=IP_BLOCK_DURATION_SECONDS)
    blocked_ips_collection.update_one({"ip": ip_address}, {"$set": {"expires_at": expires_at}}, upsert=True)

def increment_failed_attempts(hashed_id, ip_address):
    session = get_session(hashed_id)
    if not session:
        return
    
    attempts = session.get("attempts", 0) + 1
    save_session(hashed_id, session["sequence"], session["expires_at"], attempts, ip_address)

    if attempts >= MAX_FAILED_ATTEMPTS:
        block_ip(ip_address)
        delete_session(hashed_id)  

def clean_expired_sessions():
    now = datetime.utcnow()
    sessions_collection.delete_many({"expires_at": {"$lt": now}})
    print(f"Sessões expiradas limpas: {now}")

scheduler = BackgroundScheduler()

scheduler.add_job(clean_expired_sessions, IntervalTrigger(minutes=5))

scheduler.start()

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()

def generate_jwt(session_id):
    expiration_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"session_id": session_id, "exp": expiration_time}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def validate_jwt(token: str, expected_session_id: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        token_session_id = payload.get("session_id")
        if token_session_id != expected_session_id:
            raise HTTPException(status_code=401, detail="Token não corresponde à sessão.")
        return True
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido ou expirado: {str(e)}")

def encrypt_pin(pin: str) -> str:
    encrypted_pin = cipher.encrypt(pin.encode()).decode()
    return encrypted_pin

def get_decrypted_pin(user_id: str) -> str:
    user = users_collection.find_one({"user_id": user_id})
    if user:
        encrypted_pin = user.get("encrypted_pin")
        if encrypted_pin:
            return decrypt_pin(encrypted_pin)
    raise HTTPException(status_code=404, detail="Usuário não encontrado.")

def create_user(user_id: str, pin: str):
    encrypted_pin = encrypt_pin(pin)
    user_data = {
        "user_id": user_id,
        "encrypted_pin": encrypted_pin
    }
    users_collection.insert_one(user_data)

def encrypt_session_id(session_id: str) -> str:
    return cipher.encrypt(session_id.encode()).decode()

def decrypt_session_id(encrypted_session_id: str) -> str:
    try:
        return cipher.decrypt(encrypted_session_id.encode()).decode()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Sessão inválida ou corrompida")


class ValidationRequest(BaseModel):
    session_id: str
    sequence: list[list[int]]

class InvalidateSessionRequest(BaseModel):
    session_id: str

def decrypt_pin(encrypted_pin: str):
    try:
        decrypted_pin = cipher.decrypt(encrypted_pin.encode()).decode()
        return decrypted_pin
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
    
    