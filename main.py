import hashlib
import base64
import random
import secrets
from datetime import datetime, timedelta
from typing import List
from flask import jsonify, request
from pymongo import MongoClient
from cryptography.fernet import Fernet
import os
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

# Configuração do MongoDB
MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
users_collection = db["users"]

# Configuração do FastAPI
app = FastAPI()

# Configuração do cifrador
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  
MAX_SESSIONS_BEFORE_REUSE = 1000  

fernet = Fernet(FERNET_KEY)

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
BLOCK_DURATION_SECONDS = 10 
JWT_EXPIRATION_MINUTES = 3

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://10.197.75.79:3000", "http://127.0.0.1:8000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users_collection = db["users"]
sessions_collection = db["sessions"]  # Garantindo que a collection de sessões seja nomeada corretamente
blocked_ips_collection = db["blocked_ips"] 

def encrypt_numbers(numbers: list) -> list:
    hashed_numbers = [hashlib.sha256(str(num).encode('utf-8')).hexdigest() for num in numbers]
    return hashed_numbers

@app.post("/generate_session")
def generate_session():
    session_count = get_session_count()
    if session_count >= MAX_SESSIONS_BEFORE_REUSE:
        clean_old_sessions()

    session_id = secrets.token_hex(16)  
    hashed_id = hash_session_id(session_id)

    numbers = generate_random_numbers()
    encrypted_numbers = encrypt_numbers(numbers)
    expiration_time = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)

    save_session(hashed_id, numbers, expiration_time)

    return {"session_id": session_id, "sequence": encrypted_numbers, "token": generate_jwt(session_id)}


@app.post("/create_user")
def create_user():
    data = request.json
    user_id = data.get("user_id")
    pin = data.get("pin")

    if not user_id or not pin:
        return jsonify({"error": "user_id e pin são obrigatórios"}), 400

    encrypted_pin = encrypt_pin(pin)
    user_data = {
        "user_id": user_id,
        "encrypted_pin": encrypted_pin
    }

    users_collection.insert_one(user_data)
    return jsonify({"message": "Usuário criado com sucesso"}), 201

def clean_old_sessions():
    sessions_collection.delete_many({"session_id": {"$in": get_old_sessions()}})

def get_old_sessions():
    sessions = sessions_collection.find().sort("expires_at", 1)  
    old_sessions = [session["session_id"] for session in sessions[:MAX_SESSIONS_BEFORE_REUSE]]
    return old_sessions

def hash_sequence(sequence):
    if not all(isinstance(pair, list) and len(pair) == 2 for pair in sequence):
        raise ValueError("A sequência deve ser uma lista de pares (listas com 2 elementos).")
    
    sequence_str = ''.join([str(pair[0]) + str(pair[1]) for pair in sequence])
    hashed = hashlib.sha256(sequence_str.encode()).hexdigest()
    return hashed

class SequenceRequest(BaseModel):
    sequence: list  

class ValidationRequest(BaseModel):
    session_id: str
    sequence: List[str] 

import re

@app.post("/validate_sequence")
def validate_sequence(data: ValidationRequest, request: Request, authorization: str = Header(None)):
    client_ip = request.client.host

    if is_ip_blocked(client_ip):
        raise HTTPException(status_code=403, detail="Muitas tentativas falhas. Tente mais tarde.")

    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido.")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido.")

    token = authorization.split(" ")[1]

    session = sessions_collection.find_one({"session_id": hash_session_id(data.session_id)})
    if not session:
        raise HTTPException(status_code=400, detail="Sessão inválida ou expirada.")

    hash_pattern = re.compile(r'^[0-9a-fA-F]{64}$')  

    for hash_value in data.sequence:
        if not isinstance(hash_value, str) or not hash_pattern.match(hash_value):
            raise HTTPException(status_code=400, detail=f"Valor inválido na sequência: {hash_value}. Esperado um hash de 64 caracteres.")

    sessions_collection.delete_one({"session_id": hash_session_id(data.session_id)}) 

    return {"message": "Sequência validada com sucesso!"}

class InvalidateSessionRequest(BaseModel):
    session_id: str

@app.post("/invalidate_session")
def invalidate_session(data: InvalidateSessionRequest):
    try:
        decrypted_session_id = cipher.decrypt(data.session_id.encode()).decode()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Erro de decriptação. Sessão inválida ou corrompida.")
    
    hashed_id = hash_session_id(decrypted_session_id)
    if delete_session(hashed_id):
        return {"message": "Sessão invalidada."}
    return {"message": "Sessão não encontrada ou já expirada."}

def generate_random_pairs():
    numbers = list(range(1, 10)) 
    random.shuffle(numbers)
    return [[numbers[i], numbers[i + 1]] for i in range(0, len(numbers) - 1, 2)]

def generate_random_numbers():
    return [random.randint(0, 9) for _ in range(10)]  

def map_digit_to_button(digit, pairs):

    for pair in pairs:
        if digit in pair:
            return pair[0]  
    raise ValueError(f"Dígito {digit} não encontrado em nenhum botão.")

def transform_password(password, pairs):

    transformed = ""
    for digit in password:
        button_number = map_digit_to_button(int(digit), pairs)
        transformed += str(button_number) * 2  
    return transformed

def hash_session_id(session_id):
    return base64.urlsafe_b64encode(hashlib.sha256(session_id.encode()).digest()).decode()

def save_session(hashed_id, sequence, expiration_time, attempts=0, ip_address=None):
    if isinstance(sequence, str): 
        try:
            sequence = cipher.decrypt(sequence.encode()).decode()
            sequence = eval(sequence) 
        except Exception as e:
            raise HTTPException(status_code=400, detail="Erro ao descriptografar a sequência.")
    
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

def verify_user(user_id: str, plain_password: str):
    user = users_collection.find_one({"user_id": user_id})
    if user and verify_password(plain_password, user["hashed_password"]):
        return True
    return False

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

def decrypt_pin(encrypted_pin: str):
    try:
        decrypted_pin = cipher.decrypt(encrypted_pin.encode()).decode()
        return decrypted_pin
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
    
    
