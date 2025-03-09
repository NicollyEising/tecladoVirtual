import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import axios from 'axios';
import 'react-toastify/dist/ReactToastify.css';
import './api.css';

function App() {
  const [username, setUsername] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [password, setPassword] = useState([]);
  const [inputSequence, setInputSequence] = useState([]);
  const [token, setToken] = useState('');
  const [isSessionValid, setIsSessionValid] = useState(false);
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const [buttons, setButtons] = useState([]);

  // Função para gerar nova sessão
  const handleGenerateSession = async () => {
    if (!username) {
      toast.error('Por favor, insira um nome de usuário.');
      return;
    }

    try {
      const data = await generateSession(username);
      console.log('Dados recebidos da API:', data);

      if (data && data.sequence && Array.isArray(data.sequence)) {
        setSessionId(data.session_id);
        setPassword(formatSequence(data.sequence)); // Guardando a senha formatada
        setToken(data.token);
        setIsSessionValid(true);
        generateButtons(data.sequence); // Gera botões com misturados

        console.log("Token de Verificação:", data.token);
        toast.success('Sessão gerada com sucesso!');
      } else {
        toast.error('Erro: a sequência não foi retornada corretamente.');
      }
    } catch (error) {
      toast.error('Erro ao gerar sessão');
      console.error('Erro ao gerar sessão:', error);
    }
  };

  // Formata a sequência correta em pares
  const formatSequence = (sequence) => {
    let formatted = [];
    for (let i = 0; i < sequence.length; i += 2) {
      formatted.push([sequence[i], sequence[i + 1]]);
    }
    return formatted;
  };

  // Gera botões misturando os corretos com falsos
  const generateButtons = (sequence) => {
    let correctPairs = formatSequence(sequence);
    let fakePairs = generateFakePairs(correctPairs.length);

    let allButtons = [...correctPairs, ...fakePairs];
    allButtons = allButtons.sort(() => Math.random() - 0.5); // Embaralha os botões

    setButtons(allButtons);
  };

  // Gera pares falsos para confundir
  const generateFakePairs = (count) => {
    let fakePairs = [];
    while (fakePairs.length < count) {
      let num1 = Math.floor(Math.random() * 9) + 1;
      let num2 = Math.floor(Math.random() * 9) + 1;
      let newPair = [num1, num2];

      // Evita duplicação com pares corretos
      if (!fakePairs.some(pair => pair[0] === newPair[0] && pair[1] === newPair[1])) {
        fakePairs.push(newPair);
      }
    }
    return fakePairs;
  };

  // Função para validar a sequência
  const handleValidatePassword = async () => {
    try {
      const flatSequence = inputSequence.flat();

      console.log("Senha do usuário antes do envio:", flatSequence);

      const response = await axios.post('http://127.0.0.1:8000/validate_sequence', {
        session_id: sessionId,
        sequence: flatSequence,
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log("✅ Sequência validada com sucesso:", response.data);
      toast.success('Sequência validada com sucesso!');
      setIsSessionValid(false);
      setIsButtonDisabled(true);
    } catch (error) {
      console.log(error.response ? error.response.data : error.message);
      toast.error('Sequência incorreta');
    }
  };

  // Função para gerar sessão no backend
  const generateSession = async (username) => {
    const response = await axios.post('http://127.0.0.1:8000/generate_session', { username });
    console.log('Resposta da API de geração de sessão:', response.data);
    return response.data;
  };

  // Função para lidar com o clique nos botões
  const handleButtonClick = (pair) => {
    setInputSequence((prevSequence) => {
      const newSequence = [...prevSequence, pair];
      console.log("Sequência do usuário após clique:", newSequence);
      return newSequence;
    });
  };

  return (
    <div className="App">
      <h1>Teclado Virtual</h1>

      <div>
        <label htmlFor="username">Nome de Usuário:</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Digite seu nome de usuário"
        />
      </div>

      <button onClick={handleGenerateSession}>Gerar Nova Sessão</button>

      {isSessionValid ? (
        <>
          <h2>Senha Gerada:</h2>
          {password.length === 0 ? (
            <p>Carregando senha...</p>
          ) : (
            <p>{password.map(pair => `[${pair[0]},${pair[1]}]`).join(' ')}</p>
          )}

          <h2>Clique nos botões abaixo para digitar a senha:</h2>
          {buttons.length === 0 ? (
            <p>Esperando sequência...</p>
          ) : (
            <div className="buttons">
              {buttons.map((pair, index) => (
                <button
                  key={index}
                  onClick={() => handleButtonClick(pair)}
                  disabled={isButtonDisabled}
                >
                  [{pair[0]}, {pair[1]}]
                </button>
              ))}
            </div>
          )}

          <h3>Senha Selecionada:</h3>
          <p>{inputSequence.map(pair => `[${pair[0]},${pair[1]}]`).join(' ') || "Nenhuma sequência selecionada ainda..."}</p>

          <button onClick={handleValidatePassword}>Validar Senha</button>

          {/* Exibe o Token de Verificação */}
          <div>
            <h3>Token de Verificação:</h3>
            <p>{token}</p>
          </div>
        </>
      ) : null}

      <ToastContainer />
    </div>
  );
}

export default App;
