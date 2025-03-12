import os
from pymongo import MongoClient
from cryptography.fernet import Fernet

# 🔹 Configuração do banco de dados MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["teclado_virtual"]

# 🔹 Coleções do banco de dados
sessions_collection = db["sessions"]
blocked_ips_collection = db["blocked_ips"]
users_collection = db["users"]

# 🔹 Configuração de chave de criptografia AES
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key())  # Preferível armazenar como variável de ambiente
cipher = Fernet(FERNET_KEY)

# 🔹 Constantes de segurança
SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10
MAX_SESSIONS_BEFORE_REUSE = 1000
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_EXPIRATION_MINUTES = 15
