import pytest
import hashlib
from main import hash_sequence  # Importa a função hash_sequence

def test_hash_sequence_valid():
    # Caso de teste com uma sequência válida
    sequence = [[1, 2], [3, 4], [5, 6]]
    expected_hash = hashlib.sha256('123456'.encode()).hexdigest()  # O hash esperado para a sequência "123456"
    
    result = hash_sequence(sequence)
    
    # Verifica se o hash gerado corresponde ao esperado
    assert result == expected_hash, f"Esperado: {expected_hash}, mas obteve: {result}"

def test_hash_sequence_invalid():
    # Caso de teste com sequência inválida
    sequence = [[1, 2], [3, 4], 5]  # Um item não é uma lista de pares
    with pytest.raises(ValueError) as excinfo:
        hash_sequence(sequence)  # A função deve lançar um ValueError
    
    # Verifica se a mensagem do erro é a esperada
    assert str(excinfo.value) == "A sequência deve ser uma lista de pares (listas com 2 elementos)."

def test_hash_sequence_empty():
    # Caso de teste com sequência vazia
    sequence = []
    expected_hash = hashlib.sha256(''.encode()).hexdigest()  # Hash de uma string vazia
    result = hash_sequence(sequence)
    
    # Verifica se o hash gerado corresponde ao esperado
    assert result == expected_hash, f"Esperado: {expected_hash}, mas obteve: {result}"
