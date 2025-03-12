import pytest
import random
from main import generate_random_numbers  # Importe a função de gerar números aleatórios


def generate_random_numbers(lower_bound, upper_bound, count):
    # Gera uma lista de números aleatórios dentro do intervalo especificado
    return [random.randint(lower_bound, upper_bound) for _ in range(count)]

def test_generate_random_numbers_within_range():
    # Defina o intervalo esperado
    lower_bound = 1
    upper_bound = 10
    count = 5  # Defina quantos números aleatórios você quer gerar

    # Gere os números aleatórios
    result = generate_random_numbers(lower_bound, upper_bound, count)

    # Verifique se todos os números estão dentro do intervalo
    for num in result:
        assert lower_bound <= num <= upper_bound, f"Valor fora do intervalo: {num}"

def test_generate_random_numbers_count():
    # Verifique se o número de elementos gerados está correto
    lower_bound = 1
    upper_bound = 10
    count = 5

    result = generate_random_numbers(lower_bound, upper_bound, count)

    assert len(result) == count, f"Esperado {count} números, mas obteve {len(result)}"
