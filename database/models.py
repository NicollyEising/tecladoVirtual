from pydantic import BaseModel
from typing import List

# 🔹 Modelo para representar um usuário
class User(BaseModel):
    username: str
    password: str

# 🔹 Modelo para criação de sessão
class Session(BaseModel):
    session_id: str
    sequence: List[str]
    expires_at: str  # Data e hora de expiração

# 🔹 Modelo para requisições de sequência
class SequenceRequest(BaseModel):
    sequence: List[List[int]]  # Lista de pares, ex: [[1, 2], [3, 4]]

# 🔹 Modelo para validação de sequência
class ValidationRequest(BaseModel):
    session_id: str
    sequence: List[str]  # Lista de hashes dos números digitados

# 🔹 Modelo para invalidação de sessão
class InvalidateSessionRequest(BaseModel):
    session_id: str
