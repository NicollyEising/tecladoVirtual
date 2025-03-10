import hashlib
import base64
import random
import secrets
from datetime import datetime, timedelta
from pymongo import MongoClient
from cryptography.fernet import Fernet
import os
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
from bancoDeDados import *

MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]
from fastapi.middleware.cors import CORSMiddleware


FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY) 

SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  
MAX_SESSIONS_BEFORE_REUSE = 1000  


app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
BLOCK_DURATION_SECONDS = 10 
JWT_EXPIRATION_MINUTES = 15  


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate_session")
def generate_session():
    session_id = secrets.token_hex(16)
    hashed_id = hash_session_id(session_id)

    # Geração de números aleatórios (assumindo que você quer números individuais)
    numbers = generate_random_numbers()  # Pode ser uma lista de números em vez de pares
    expiration_time = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)

    save_session(hashed_id, numbers, expiration_time)
    encrypted_session_id = cipher.encrypt(session_id.encode()).decode()

    return {"session_id": encrypted_session_id, "sequence": numbers, "token": generate_jwt(session_id)}


@app.post("/validate_sequence")
def validate_sequence(data: ValidationRequest, request: Request, authorization: str = Header(None)):
    client_ip = request.client.host

    if is_ip_blocked(client_ip):
        raise HTTPException(status_code=403, detail="Muitas tentativas falhas. Tente mais tarde.")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido.")
    
    token = authorization.split(" ")[1]
    
    try:
        decrypted_session_id = cipher.decrypt(data.session_id.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Erro ao decriptografar sessão.")
    
    hashed_id = hash_session_id(decrypted_session_id)
    session = get_session(hashed_id)

    if not session or session["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Sessão inválida ou expirada.")

    # 🔹 Proteção contra força bruta
    if session["sequence"] != [num for pair in data.sequence for num in pair]:
        attempts = session.get("attempts", 0) + 1
        save_session(hashed_id, session["sequence"], session["expires_at"], attempts, client_ip)
        
        if attempts >= MAX_FAILED_ATTEMPTS:
            block_ip(client_ip)
            raise HTTPException(status_code=403, detail="Muitas tentativas falhas. IP bloqueado.")
        
        raise HTTPException(status_code=400, detail="Sequência incorreta.")

    sessions_collection.delete_one({"session_id": hashed_id})

    return {"message": "Sequência validada com sucesso."}


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
