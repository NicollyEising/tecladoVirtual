import hashlib
import base64
import random
import secrets
from datetime import datetime, timedelta
from typing import List
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

fernet = Fernet(FERNET_KEY)

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
BLOCK_DURATION_SECONDS = 10 
JWT_EXPIRATION_MINUTES = 3


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos os domínios
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

def encrypt_numbers(numbers: list) -> list:
    hashed_numbers = [hashlib.sha256(str(num).encode('utf-8')).hexdigest() for num in numbers]
    return hashed_numbers


@app.post("/generate_session")
def generate_session():
    # Verificar se o limite de sessões foi atingido
    session_count = get_session_count()
    if session_count >= MAX_SESSIONS_BEFORE_REUSE:
        # Se o limite foi atingido, removemos as sessões mais antigas
        clean_old_sessions()

    session_id = secrets.token_hex(16)  # Gera o session_id diretamente
    hashed_id = hash_session_id(session_id)

    # Geração de números aleatórios
    numbers = generate_random_numbers()
    encrypted_numbers = encrypt_numbers(numbers)
    expiration_time = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)

    save_session(hashed_id, numbers, expiration_time)

    return {"session_id": session_id, "sequence": encrypted_numbers, "token": generate_jwt(session_id)}

def clean_old_sessions():
    # Limpeza das sessões antigas (se o limite de 1000 for atingido)
    sessions_collection.delete_many({"session_id": {"$in": get_old_sessions()}})

def get_old_sessions():
    # Obtém as sessões mais antigas (criação de um critério de expiração ou prioridade de remoção)
    sessions = sessions_collection.find().sort("expires_at", 1)  # Ordena por tempo de expiração crescente
    old_sessions = [session["session_id"] for session in sessions[:MAX_SESSIONS_BEFORE_REUSE]]
    return old_sessions


def hash_sequence(sequence):
    # Verifica se a sequência é uma lista de pares (listas com 2 elementos)
    if not all(isinstance(pair, list) and len(pair) == 2 for pair in sequence):
        raise ValueError("A sequência deve ser uma lista de pares (listas com 2 elementos).")
    
    # Realiza o hash da sequência
    sequence_str = ''.join([str(pair[0]) + str(pair[1]) for pair in sequence])
    hashed = hashlib.sha256(sequence_str.encode()).hexdigest()
    return hashed

# Gerando uma sequência de números

class SequenceRequest(BaseModel):
    sequence: list  # A sequência pode ser uma lista de pares, como [[1, 2], [3, 4]]


class ValidationRequest(BaseModel):
    session_id: str
    sequence: List[str] 

import re

@app.post("/validate_sequence")
def validate_sequence(data: ValidationRequest, request: Request, authorization: str = Header(None)):
    client_ip = request.client.host

    # 1️⃣ Verifique se o IP está bloqueado
    if is_ip_blocked(client_ip):
        raise HTTPException(status_code=403, detail="Muitas tentativas falhas. Tente mais tarde.")

    # 2️⃣ Verifique se o token foi enviado corretamente
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido.")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido ou inválido.")

    token = authorization.split(" ")[1]

    session = sessions_collection.find_one({"session_id": hash_session_id(data.session_id)})
    if not session:
        raise HTTPException(status_code=400, detail="Sessão inválida ou expirada.")

    # 3️⃣ Verifique se cada item da sequência é um hash válido
    hash_pattern = re.compile(r'^[0-9a-fA-F]{64}$')  # Regex para validar um hash de 64 caracteres

    for hash_value in data.sequence:
        if not isinstance(hash_value, str) or not hash_pattern.match(hash_value):
            raise HTTPException(status_code=400, detail=f"Valor inválido na sequência: {hash_value}. Esperado um hash de 64 caracteres.")

    # Remover a sessão após validação bem-sucedida
    sessions_collection.delete_one({"session_id": hash_session_id(data.session_id)})  # Remover a sessão

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



# 🔹 Função para gerar pares de números aleatórios
def generate_random_pairs():
    numbers = list(range(1, 10))  # Números de 1 a 9
    random.shuffle(numbers)
    return [[numbers[i], numbers[i + 1]] for i in range(0, len(numbers) - 1, 2)]

def generate_random_numbers():
    return [random.randint(0, 9) for _ in range(10)]  # Exemplo, você pode ajustar conforme necessário


# 🔹 Função para mapear um dígito para o botão correspondente
def map_digit_to_button(digit, pairs):
    """
    Mapeia um dígito para o botão correspondente (par de números).
    Retorna o primeiro número do par que contém o dígito.
    """
    for pair in pairs:
        if digit in pair:
            return pair[0]  # Retorna o primeiro número do par como representante do botão
    raise ValueError(f"Dígito {digit} não encontrado em nenhum botão.")

# 🔹 Função para transformar a senha em sequência de botões
def transform_password(password, pairs):
    """
    Transforma a senha original em uma sequência de botões.
    Exemplo: "12345" → "112233" com pares [1,2], [3,4], [5,6].
    """
    transformed = ""
    for digit in password:
        button_number = map_digit_to_button(int(digit), pairs)
        transformed += str(button_number) * 2  # Cada botão é "pressionado" duas vezes
    return transformed

# 🔹 Função para gerar hash do ID de sessão
def hash_session_id(session_id):
    return base64.urlsafe_b64encode(hashlib.sha256(session_id.encode()).digest()).decode()

# 🔹 Função para salvar a sessão no banco de dados
def save_session(hashed_id, sequence, expiration_time, attempts=0, ip_address=None):
    # Verifica se a sequência está criptografada e, se necessário, descriptografa
    if isinstance(sequence, str):  # Verifica se a sequência é uma string (significando que ela está criptografada)
        try:
            sequence = cipher.decrypt(sequence.encode()).decode()
            sequence = eval(sequence)  # Converte de volta para a lista (importante para segurança)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Erro ao descriptografar a sequência.")
    
    # Armazena os dados descriptografados no banco de dados
    session_data = {
        "session_id": hashed_id,
        "sequence": sequence,  # Aqui já está descriptografada
        "expires_at": expiration_time,
        "attempts": attempts,
        "ip_address": ip_address
    }
    sessions_collection.update_one({"session_id": hashed_id}, {"$set": session_data}, upsert=True)


class User(BaseModel):
    username: str
    password: str

# 🔹 Criação do objeto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔹 Função para hash da senha
def hash_password(password: str):
    return pwd_context.hash(password)

# Função para verificar a senha
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# When verifying user login
def verify_user(user_id: str, plain_password: str):
    user = users_collection.find_one({"user_id": user_id})
    if user and verify_password(plain_password, user["hashed_password"]):
        return True
    return False

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
    if blocked_ip and blocked_ip["expires_at"] > datetime.utcnow():
        return True
    return False


# 🔹 Função para bloquear um IP após tentativas falhas
# Função para bloquear um IP após tentativas falhas
def block_ip(ip_address):
    expires_at = datetime.utcnow() + timedelta(seconds=IP_BLOCK_DURATION_SECONDS)
    blocked_ips_collection.update_one({"ip": ip_address}, {"$set": {"expires_at": expires_at}}, upsert=True)


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

# 🔹 Função para limpar sessões expiradas automaticamente
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

def encrypt_pin(pin: str) -> str:
    encrypted_pin = cipher.encrypt(pin.encode()).decode()
    return encrypted_pin

# Função para recuperar o PIN criptografado do banco de dados e descriptografar
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


# 🔹 Modelo para requisições de validação



def decrypt_pin(encrypted_pin: str):
    try:
        # Tentando descriptografar
        decrypted_pin = cipher.decrypt(encrypted_pin.encode()).decode()
        return decrypted_pin
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
    
    
