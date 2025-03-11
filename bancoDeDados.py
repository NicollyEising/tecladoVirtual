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
