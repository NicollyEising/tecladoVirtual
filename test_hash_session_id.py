import hashlib
import pytest
from main import hash_session_id  # Importe a função hash_session_id

def hash_session_id(session_id: str) -> str:
    # Gera o hash SHA-256 para o session_id fornecido
    return hashlib.sha256(session_id.encode()).hexdigest()

def test_hash_session_id():
    # Teste com um session_id conhecido
    session_id = "1234567890"  # Um session_id de exemplo
    expected_hash = hashlib.sha256(session_id.encode()).hexdigest()  # O hash esperado para o session_id
    
    # Chama a função para gerar o hash do session_id
    result = hash_session_id(session_id)
    
    # Verifica se o hash gerado é o esperado
    assert result == expected_hash, f"Esperado: {expected_hash}, mas obteve: {result}"
