import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from pymongo import MongoClient
from cryptography.fernet import Fernet
from config import SESSION_EXPIRATION_MINUTES, MAX_SESSIONS_BEFORE_REUSE, IP_BLOCK_DURATION_SECONDS
from database import sessions_collection, blocked_ips_collection

# 🔹 Chave de criptografia
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

# 🔹 Gera um ID de sessão seguro e criptografado
def generate_session_id():
    return secrets.token_hex(16)

# 🔹 Hashea o ID da sessão para armazenamento seguro
def hash_session_id(session_id):
    return base64.urlsafe_b64encode(hashlib.sha256(session_id.encode()).digest()).decode()

# 🔹 Salva uma nova sessão no banco de dados
def save_session(session_id, sequence, expiration_time, attempts=0, ip_address=None):
    hashed_id = hash_session_id(session_id)
    session_data = {
        "session_id": hashed_id,
        "sequence": sequence,
        "expires_at": expiration_time,
        "attempts": attempts,
        "ip_address": ip_address
    }
    sessions_collection.update_one({"session_id": hashed_id}, {"$set": session_data}, upsert=True)

# 🔹 Obtém uma sessão pelo ID hashado
def get_session(hashed_id):
    return sessions_collection.find_one({"session_id": hashed_id})

# 🔹 Deleta uma sessão do banco de dados
def delete_session(hashed_id):
    result = sessions_collection.delete_one({"session_id": hashed_id})
    return result.deleted_count > 0

# 🔹 Conta o número total de sessões ativas
def get_session_count():
    return sessions_collection.count_documents({})

# 🔹 Limpa sessões antigas quando o limite for atingido
def clean_old_sessions():
    sessions_collection.delete_many({"session_id": {"$in": get_old_sessions()}})

# 🔹 Obtém as sessões mais antigas para remoção
def get_old_sessions():
    sessions = sessions_collection.find().sort("expires_at", 1)  
    return [session["session_id"] for session in sessions[:MAX_SESSIONS_BEFORE_REUSE]]

# 🔹 Verifica se um IP está bloqueado
def is_ip_blocked(ip_address):
    blocked_ip = blocked_ips_collection.find_one({"ip": ip_address})
    return blocked_ip and blocked_ip["expires_at"] > datetime.utcnow()

# 🔹 Bloqueia um IP após muitas tentativas falhas
def block_ip(ip_address):
    expires_at = datetime.utcnow() + timedelta(seconds=IP_BLOCK_DURATION_SECONDS)
    blocked_ips_collection.update_one({"ip": ip_address}, {"$set": {"expires_at": expires_at}}, upsert=True)

# 🔹 Incrementa tentativas de falha e bloqueia IP se necessário
def increment_failed_attempts(hashed_id, ip_address):
    session = get_session(hashed_id)
    if not session:
        return
    
    attempts = session.get("attempts", 0) + 1
    save_session(hashed_id, session["sequence"], session["expires_at"], attempts, ip_address)

    if attempts >= 3:  # Número máximo de tentativas antes do bloqueio
        block_ip(ip_address)
        delete_session(hashed_id)  

# 🔹 Limpa sessões expiradas automaticamente
def clean_expired_sessions():
    now = datetime.utcnow()
    sessions_collection.delete_many({"expires_at": {"$lt": now}})
