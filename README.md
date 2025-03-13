# Projeto Teclado Virtual - Backend e Frontend

Este projeto consiste em um sistema de autenticação seguro baseado em um teclado virtual, utilizando FastAPI para o backend e React para o frontend. O MongoDB é usado para armazenamento dos dados dos usuários.

## Requisitos

- Python 3.11+
- Node.js 14+
- MongoDB

## Configuração do Ambiente

1. Executar start.bat
* Função: O arquivo start.bat pode ser utilizado para iniciar o processo de execução do sistema.
* Execução: Basta rodar o script start.bat para configurar e iniciar os serviços necessários.

### Backend

1. Instale as dependências do backend:

* pip install -r requirements.txt

2. Inicie o servidor backend:

* uvicorn main:app --host 0.0.0.0 --port 8000

### Frontend

1. Navegue até a pasta do frontend:

* cd frontend

2. Instale as dependências do frontend:

* npm install

3. Inicie o servidor React:

* npm start

## Configuração do MongoDB

O projeto utiliza um banco MongoDB hospedado na nuvem. Para configurar a conexão, edite a variável `MONGO_URI` no código do backend:

* MONGO_URI = "mongodb+srv://<seu_email>:<sua_senha>@cluster0.9xwlq.mongodb.net/"


## Segurança

O sistema implementa diversas camadas de segurança:

- Uso de JWT para autenticação das sessões.
- Hashing de senhas e PINs com bcrypt e Fernet.
- Bloqueio de IPs após múltiplas tentativas falhas.
- Expiração automática de sessões.

## Endpoints Principais

### Criar Usuário

- **Endpoint**: `POST /create_user`
- **Entrada**: `{
  "user_id": "user123",
  "pin": "1234"
}`



### Gerar Sessão

- **Endpoint**: `POST /generate_session`
- **Saída**: `{
 {"session_id": "abc123", "sequence": ["hash1", "hash2"], "token": "jwt_token"}`


- **Endpoint**: POST /validate_sequence
- **Saída**: `{"message": "Sequência validada com sucesso!"}`

### Validar Sequência

- **Endpoint**: `POST /create_user`
- **Entrada**: `{
  "user_id": "user123",
  "pin": "1234"
}`


