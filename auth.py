import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from utils import generate_session_id, hash_session_id
from database.session_manager import SessionManager

# 🔹 Configuração do JWT
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_EXPIRATION_MINUTES = 3
ALGORITHM = "HS256"

# 🔹 Inicializa o gerenciador de sessão
session_manager = SessionManager()

# 🔹 Função para gerar um token JWT
def generate_jwt(session_id):
    expiration_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"session_id": session_id, "exp": expiration_time}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# 🔹 Função para validar um token JWT
def validate_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        session_id = payload.get("session_id")

        if not session_manager.is_valid_session(session_id):
            return None  # Sessão inválida ou expirada

        return session_id
    except JWTError:
        return None

# 🔹 Função para autenticar usuário (caso tenha login)
def authenticate_user(username: str, password: str):
    user = session_manager.get_user(username)
    
    if user and user["password"] == hash_session_id(password):  # Senha já está hasheada no banco
        session_id = generate_session_id()
        session_manager.create_session(session_id, username)
        token = generate_jwt(session_id)
        return token
    
    return None

# 🔹 Função para logout (invalida a sessão do usuário)
def logout(session_id):
    session_manager.invalidate_session(session_id)
