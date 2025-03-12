import pytest
import hashlib
from main import encrypt_numbers

def test_encrypt_numbers():
    # Entrada: lista de números
    numbers = [1, 2, 3, 4, 5]
    
    # Chama a função
    encrypted = encrypt_numbers(numbers)
    
    # Verifica se a saída tem o mesmo tamanho da entrada
    assert len(encrypted) == len(numbers)
    
    # Verifica se cada elemento é um hash SHA-256
    for original, hashed in zip(numbers, encrypted):
        expected_hash = hashlib.sha256(str(original).encode('utf-8')).hexdigest()
        assert hashed == expected_hash