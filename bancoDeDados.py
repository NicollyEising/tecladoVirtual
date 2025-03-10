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

# 🔹 Configuração do banco de dados MongoDB
MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]
users_collection = db["users"]

# 🔹 Configuração de chave de criptografia AES (agora armazenada com segurança)
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

# 🔹 Configurações de segurança
SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  # Alterado para 10 segundos
MAX_SESSIONS_BEFORE_REUSE = 1000  # Limite de sessões ativas

# 🔹 Configurações do FastAPI
app = FastAPI()

# 🔹 Configurações de segurança e validade
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_EXPIRATION_MINUTES = 15  # Tempo de expiração do JWT

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

# 🔹 Criação do objeto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔹 Função para hash da senha
def hash_password(password: str):
    return pwd_context.hash(password)

# Função para verificar a senha
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

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
class ValidationRequest(BaseModel):
    session_id: str
    sequence: list[list[int]]


class InvalidateSessionRequest(BaseModel):
    session_id: str


def decrypt_pin(encrypted_pin: str):
    try:
        # Tentando descriptografar
        decrypted_pin = cipher.decrypt(encrypted_pin.encode()).decode()
        return decrypted_pin
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
    
    