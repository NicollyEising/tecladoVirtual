import os
from cryptography.fernet import Fernet

# 🔹 Configurações do Banco de Dados
MONGO_URI = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
DB_NAME = "teclado_virtual"

# config.py
DATABASE_URL = "mongodb+srv://nicollymunhozeising85:RRSAkX1DsOd5MRVO@cluster0.9xwlq.mongodb.net/"
DATABASE_NAME = "teclado_virtual"

# 🔹 Configurações de Segurança
SESSION_EXPIRATION_MINUTES = 5
MAX_FAILED_ATTEMPTS = 3
IP_BLOCK_DURATION_SECONDS = 10
MAX_SESSIONS_BEFORE_REUSE = 1000

# 🔹 Configuração de criptografia
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key())  # Use variável de ambiente em produção
cipher = Fernet(FERNET_KEY)

# 🔹 Configurações de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_EXPIRATION_MINUTES = 15
JWT_ALGORITHM = "HS256"

# 🔹 Configuração do CORS
ALLOWED_ORIGINS = ["*", "http://10.197.75.79:3000", "http://127.0.0.1:8000"]
