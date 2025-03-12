from pymongo import MongoClient
from config import DATABASE_URL, DATABASE_NAME

# Conexão com o banco de dados
client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]

# Definição das coleções
sessoes = db["sessoes"]
usuarios = db["usuarios"]
tentativas_falhas = db["tentativas_falhas"]

def init_db():
    """Inicializa o banco de dados, garantindo que os índices necessários existam."""
    sessoes.create_index("session_id", unique=True)
    sessoes.create_index("expiration_time", expireAfterSeconds=0)
    usuarios.create_index("username", unique=True)
    tentativas_falhas.create_index("ip_address", unique=True)

    print("Banco de dados inicializado com sucesso!")

