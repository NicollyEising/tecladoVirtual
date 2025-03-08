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

# 🔹 Configuração do banco de dados MongoDB
MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]

# 🔹 Configuração de chave de criptografia AES (agora armazenada com segurança)
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY) 

# 🔹 Configurações de segurança
SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  # Alterado para 10 segundos
MAX_SESSIONS_BEFORE_REUSE = 1000  # Defina o valor desejado para limitar o número de sessões


# 🔹 Configurações do FastAPI
app = FastAPI()

# 🔹 Configurações de segurança e validade
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
BLOCK_DURATION_SECONDS = 10  # Alterado para 10 segundos (apenas para referência, não usado diretamente aqui)
JWT_EXPIRATION_MINUTES = 15  # Configuração do tempo de expiração do JWT

# 🔹 Função para gerar pares de números aleatórios
def generate_random_pairs():
    numbers = list(range(1, 10))  # Números de 1 a 9
    random.shuffle(numbers)  # Embaralha os números
    pairs = [(numbers[i], numbers[i + 1]) for i in range(0, len(numbers) - 1, 2)]  # Cria pares consecutivos
    return pairs

# 🔹 Função para gerar hash do ID de sessão
def hash_session_id(session_id):
    return base64.urlsafe_b64encode(hashlib.sha256(session_id.encode()).digest()).decode()

# 🔹 Função para salvar a sessão no banco de dados
def save_session(hashed_id, sequence, expiration_time, attempts=0, ip_address=None):
    session_data = {
        "session_id": hashed_id,
        "sequence": sequence,
        "expires_at": expiration_time,
        "attempts": attempts,
        "ip_address": ip_address
    }

    sessions_collection.update_one(
        {"session_id": hashed_id},
        {"$set": session_data},
        upsert=True
    )

# 🔹 Função para recuperar uma sessão pelo ID hashado
def get_session(hashed_id):
    return sessions_collection.find_one({"session_id": hashed_id})

# 🔹 Função para deletar uma sessão
def delete_session(hashed_id):
    result = sessions_collection.delete_one({"session_id": hashed_id})
    return result.deleted_count > 0

# 🔹 Função para contar o número total de sessões ativas
def get_session_count():
    return sessions_collection.count_documents({})

# 🔹 Função para verificar se um IP está bloqueado
def is_ip_blocked(ip_address):
    blocked_ip = blocked_ips_collection.find_one({"ip": ip_address})
    if blocked_ip:
        # Verifica se o bloqueio já expirou
        if blocked_ip["expires_at"] < datetime.utcnow():
            blocked_ips_collection.delete_one({"ip": ip_address})
            return False
        return True
    return False

# 🔹 Função para bloquear um IP após tentativas falhas
def block_ip(ip_address):
    expires_at = datetime.utcnow() + timedelta(seconds=IP_BLOCK_DURATION_SECONDS)  # Alterado para segundos
    blocked_ips_collection.update_one(
        {"ip": ip_address},
        {"$set": {"ip": ip_address, "expires_at": expires_at}},
        upsert=True
    )

# 🔹 Função para incrementar tentativas de falha e bloquear IP se necessário
def increment_failed_attempts(hashed_id, ip_address):
    session = get_session(hashed_id)
    if not session:
        return
    
    attempts = session.get("attempts", 0) + 1
    save_session(hashed_id, session["sequence"], session["expires_at"], attempts, ip_address)

    if attempts >= MAX_FAILED_ATTEMPTS:
        block_ip(ip_address)
        delete_session(hashed_id)  # Remove a sessão após atingir o limite de tentativas

# 🔹 Função para limpar sessões expiradas automaticamente (movida para tarefa agendada)
def clean_expired_sessions():
    now = datetime.utcnow()
    sessions_collection.delete_many({"expires_at": {"$lt": now}})

# 🔹 Gera token JWT para segurança opcional
def generate_jwt(session_id):
    expiration_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"session_id": session_id, "exp": expiration_time}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 🔹 Função para validar o JWT
def validate_jwt(token: str, expected_session_id: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        token_session_id = payload.get("session_id")
        if token_session_id != expected_session_id:
            raise HTTPException(status_code=401, detail="Token não corresponde à sessão.")
        return True
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido ou expirado: {str(e)}")

# 🔹 Modelo para requisições de validação
class ValidationRequest(BaseModel):
    session_id: str
    sequence: list[list[int]]  # Aceita uma lista de listas de inteiros

class InvalidateSessionRequest(BaseModel):
    session_id: str

# 🔹 Endpoint para gerar uma nova sessão
@app.post("/generate_session")
def generate_session():
    clean_expired_sessions()  # Limpa sessões expiradas antes de criar uma nova
    session_id = secrets.token_hex(16)
    hashed_id = hash_session_id(session_id)

    # Verifica o limite de reutilização de sessões
    session_count = get_session_count()
    if session_count >= MAX_SESSIONS_BEFORE_REUSE:
        raise HTTPException(status_code=400, detail="Limite de sessões atingido, tente novamente mais tarde.")
    
    pairs = generate_random_pairs()
    correct_sequence = [num for pair in pairs for num in pair]
    expiration_time = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)

    save_session(hashed_id, correct_sequence, expiration_time)
    encrypted_session_id = cipher.encrypt(session_id.encode()).decode()
    
    return {"session_id": encrypted_session_id, "sequence": pairs, "token": generate_jwt(session_id)}

# 🔹 Endpoint para validar a sequência
@app.post("/validate_sequence")
def validate_sequence(data: ValidationRequest, request: Request, authorization: str = Header(None)):
    client_ip = request.client.host

    # Verifica se o IP está bloqueado
    if is_ip_blocked(client_ip):
        raise HTTPException(status_code=403, detail="Muitas tentativas falhas. Tente novamente mais tarde.")
    
    # Verifica se o token JWT foi fornecido
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido.")
    
    token = authorization.split(" ")[1]
    
    # Tenta descriptografar o ID da sessão
    try:
        decrypted_session_id = cipher.decrypt(data.session_id.encode()).decode()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Erro de decriptação. Sessão inválida ou corrompida.")
    
    # Valida o JWT e verifica se corresponde ao session_id
    validate_jwt(token, decrypted_session_id)
    
    # Recupera a sessão usando o ID hashado
    hashed_id = hash_session_id(decrypted_session_id)
    session = get_session(hashed_id)
    
    # Verifica se a sessão existe e está válida
    if not session or session["expires_at"] < datetime.utcnow():
        delete_session(hashed_id)
        raise HTTPException(status_code=400, detail="Sessão inválida ou expirada.")
    
    # "Achata" a lista de listas enviada pelo cliente
    flattened_sequence = [num for pair in data.sequence for num in pair]
    
    # Verifica se a sequência enviada é igual à sequência correta
    if session["sequence"] != flattened_sequence:
        increment_failed_attempts(hashed_id, client_ip)
        raise HTTPException(status_code=400, detail="Sequência incorreta.")
    
    # Se a sequência estiver correta, invalida a sessão
    delete_session(hashed_id)
    return {"message": "Sequência validada com sucesso."}

# 🔹 Endpoint para invalidar uma sessão manualmente
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
