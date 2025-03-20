@echo off

:: Instalar as dependências do backend (Python)
pip install -r requirements.txt

:: Iniciar o servidor backend em um novo terminal
start cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000"

:: Aguardar um pouco para garantir que o backend está rodando
timeout /t 3

:: Entrar no diretório do frontend
cd frontend
npm start
