import pytest
from fastapi.testclient import TestClient
from main import app  # Certifique-se de importar o seu aplicativo FastAPI corretamente
from datetime import datetime, timedelta
import jwt
from jose import JWTError

client = TestClient(app)

# Teste de Integração para a rota /generate_session
def test_generate_session():
    # Envia a requisição para gerar uma sessão
    response = client.post("/generate_session")
    
    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200
    
    # Verifica se a resposta contém um session_id, sequência criptografada e token JWT
    data = response.json()
    assert "session_id" in data
    assert "sequence" in data
    assert "token" in data
    
    # Verifica se o JWT gerado é válido
    try:
        payload = jwt.decode(data["token"], "supersecretkey", algorithms=["HS256"])
        assert payload["session_id"] == data["session_id"]
        assert "exp" in payload  # Verifica se a data de expiração está presente
    except JWTError:
        assert False, "Token JWT inválido"

# Teste de Integração para a rota /validate_sequence
def test_validate_sequence():
    # Gerar uma sessão primeiro
    session_response = client.post("/generate_session")
    assert session_response.status_code == 200
    session_data = session_response.json()
    session_id = session_data["session_id"]
    encrypted_sequence = session_data["sequence"]
    
    # Criar o token JWT válido
    token = session_data["token"]
    
    # Envia a requisição para validar a sequência
    validation_data = {
        "session_id": session_id,
        "sequence": encrypted_sequence
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/validate_sequence", json=validation_data, headers=headers)
    
    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200
    
    # Verifica se a mensagem de sucesso foi retornada
    data = response.json()
    assert data["message"] == "Sequência validada com sucesso!"

