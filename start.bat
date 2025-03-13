@echo off

:: Instalar as dependências do backend (Python)
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000
:: Instalar as dependências do frontend (Node.js)
cd frontend

:: Iniciar o servidor backend

:: Entrar no diretório do frontend e iniciar o React
cd frontend
npm start
