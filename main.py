import hashlib
import base64
import random
import secrets
from datetime import datetime, timedelta
import uuid
from pymongo import MongoClient
from cryptography.fernet import Fernet
import os
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from bancoDeDados import *
import ssl
from fastapi.middleware.cors import CORSMiddleware

MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]



FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY) 

SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  
MAX_SESSIONS_BEFORE_REUSE = 1000  

app = FastAPI()

# Rota simples de exemplo
@app.get("/")
def read_root():
    return {"message": "Olá, Mundo!"}

# Configuração SSL para HTTPS
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")


    
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
BLOCK_DURATION_SECONDS = 10 
JWT_EXPIRATION_MINUTES = 15  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate_session")
def generate_session():
    session_id = str(uuid.uuid4())  # Exemplo de geração do ID de sessão
    encrypted_session_id = encrypt_session_id(session_id)
    hashed_id = hash_session_id(session_id)

    numbers = generate_random_numbers() 
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


@app.post("/clean_sessions")
def clean_sessions(background_tasks: BackgroundTasks):
    background_tasks.add_task(clean_expired_sessions)
    return {"message": "Limpeza das sessões foi agendada."}

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

## pem phrase = nao sei

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Se sua aplicação se chama 'main.py' e a instância FastAPI é 'app'
        host="0.0.0.0",
        port=443,
        ssl_keyfile="server.key",  # Caminho para a chave privada
        ssl_certfile="server.crt",  # Caminho para o certificado
    )