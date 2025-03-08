import hashlib
import base64
import random
import secrets
from datetime import datetime, timedelta
from pymongo import MongoClient
from cryptography.fernet import Fernet

# 🔹 Configuração do banco de dados MongoDB
MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]

# 🔹 Chave de criptografia AES (deve ser armazenada com segurança)
AES_KEY = Fernet.generate_key()
cipher = Fernet(AES_KEY)

# 🔹 Configurações de segurança
SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10  # Alterado para 10 segundos

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

# 🔹 Função para limpar sessões expiradas automaticamente
def clean_expired_sessions():
    now = datetime.utcnow()
    sessions_collection.delete_many({"expires_at": {"$lt": now}})