import hashlib
import base64
import random
import secrets
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import re

# 🔹 Configuração do JWT
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_EXPIRATION_MINUTES = 3

# 🔹 Configuração da criptografia
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)

# 🔹 Função para gerar hash de uma sequência
def hash_sequence(sequence):
    if not all(isinstance(pair, list) and len(pair) == 2 for pair in sequence):
        raise ValueError("A sequência deve ser uma lista de pares (listas com 2 elementos).")
    
    sequence_str = ''.join([str(pair[0]) + str(pair[1]) for pair in sequence])
    return hashlib.sha256(sequence_str.encode()).hexdigest()

# 🔹 Função para criptografar um PIN
def encrypt_pin(pin: str) -> str:
    return cipher.encrypt(pin.encode()).decode()

# 🔹 Função para descriptografar um PIN
def decrypt_pin(encrypted_pin: str) -> str:
    try:
        return cipher.decrypt(encrypted_pin.encode()).decode()
    except Exception:
        raise ValueError("Erro ao descriptografar o PIN.")

# 🔹 Função para gerar um session_id seguro
def generate_session_id():
    return secrets.token_hex(16)

# 🔹 Função para hashear um session_id
def hash_session_id(session_id):
    return base64.urlsafe_b64encode(hashlib.sha256(session_id.encode()).digest()).decode()

# 🔹 Função para gerar números aleatórios
def generate_random_numbers():
    return [random.randint(0, 9) for _ in range(10)]

# 🔹 Função para validar se um hash segue o padrão esperado
def is_valid_hash(hash_value):
    hash_pattern = re.compile(r'^[0-9a-fA-F]{64}$')
    return bool(hash_pattern.match(hash_value))

# 🔹 Função para gerar um token JWT
def generate_jwt(session_id):
    expiration_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"session_id": session_id, "exp": expiration_time}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 🔹 Função para validar um token JWT
def validate_jwt(token: str, expected_session_id: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("session_id") != expected_session_id:
            return False
        return True
    except JWTError:
        return False
