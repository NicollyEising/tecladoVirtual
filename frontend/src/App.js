import React, { useState } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import axios from 'axios';
import 'react-toastify/dist/ReactToastify.css';
import './api.css';
import CryptoJS from 'crypto-js';  // Importe a biblioteca CryptoJS

import https from 'https';

const agent = new https.Agent({  
  rejectUnauthorized: false  // Ignora erros de certificado
});

const response = await axios.post(`${apiUrl}/generate_session`, { username }, {
  httpsAgent: agent
});


function App() {
  const [username, setUsername] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [password, setPassword] = useState([]);
  const [inputSequence, setInputSequence] = useState([]);
  const [token, setToken] = useState('');
  const [isSessionValid, setIsSessionValid] = useState(false);
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const [buttons, setButtons] = useState([]);

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
        setPassword(formatSequence(data.sequence)); 
        setToken(data.token);
        setIsSessionValid(true);
        generateButtons(data.sequence); 

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

  const formatSequence = (sequence) => {
    let formatted = [];
    for (let i = 0; i < sequence.length; i += 2) {
      formatted.push([sequence[i], sequence[i + 1]]);
    }
    return formatted;
  };

  const generateButtons = (sequence) => {
    let correctPairs = [];
    
    for (let i = 0; i < sequence.length; i += 2) {
      let num1 = sequence[i];
      let num2 = sequence[i + 1];
      
      correctPairs.push([num1, num2]);
    }

    let allButtons = [];
    correctPairs.forEach(pair => {
      allButtons.push(pair);
    });

    for (let i = 0; i < correctPairs.length; i++) {
      let num1 = Math.floor(Math.random() * 10);  
      let num2 = Math.floor(Math.random() * 10);
      allButtons.push([num1, num2]);
    }

    allButtons = allButtons.sort(() => Math.random() - 0.5);

    setButtons(allButtons);
  };

  const displayButtons = () => {
    if (buttons.length === 0) return <p>Esperando sequência...</p>;

    return (
      <div className="buttons">
        {buttons.map((pair, index) => (
          <button
            key={index}
            onClick={() => handleButtonClick(pair)} 
            disabled={isButtonDisabled}
          >
            [{pair[0]} ou {pair[1]}]
          </button>
        ))}
      </div>
    );
  };

  const apiUrl = "https://127.0.0.1:443";  // Use 127.0.0.1 para localhost
  // Certifique-se de usar o endereço correto


  // URL com HTTPS

  const handleValidatePassword = async () => {
    try {
      const formattedSequence = [];
      for (let i = 0; i < inputSequence.length; i += 2) {
        formattedSequence.push([inputSequence[i], inputSequence[i + 1]]);
      }

      const isSequenceCorrect = formattedSequence.every((pair, index) => {
        return pair[0] === password[index][0] && pair[1] === password[index][1];
      });

      if (!isSequenceCorrect) {
        toast.error('Sequência incorreta');
        return;
      }

      const response = await axios.post(`https://0.0.0.1:443/validate_sequence`, {
        httpsAgent: new https.Agent({ rejectUnauthorized: false }), // vírgula aqui
        session_id: sessionId,
        sequence: formattedSequence,
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
      console.log('Error response:', error.response ? error.response.data : error.message);
      toast.error('Erro ao validar a sequência');
    }
  };

  const handleButtonClick = (pair) => {
    const flatPassword = password.flat();  // Cria uma lista plana da senha
    const nextExpectedNumber = flatPassword[inputSequence.length];  // Obtém o próximo número esperado
    
    const isValid = pair.includes(nextExpectedNumber);  // Verifica se o número selecionado está no par
  
    if (isValid) {
      setInputSequence((prevSequence) => {
        const newSequence = [...prevSequence, nextExpectedNumber];
        console.log("Sequência do usuário após clique:", newSequence);
        return newSequence;
      });
    } else {
      toast.error(`Número ${nextExpectedNumber} não está no par. Tente novamente.`);
    }
  };

  const generateSession = async (username) => {
    const response = await axios.post(`${apiUrl}/generate_session`, { username });


    
    // Criptografando o ID de Sessão antes de usá-lo
    const encryptedSessionId = encryptSessionId(response.data.session_id);
    
    setSessionId(encryptedSessionId);
    setPassword(formatSequence(response.data.sequence));
    setToken(response.data.token);
    
    console.log('ID da sessão criptografado:', encryptedSessionId);
    
    return response.data;
  };

  const encryptSessionId = (sessionId) => {
    // Use CryptoJS para criptografar o ID de Sessão
    const encrypted = CryptoJS.AES.encrypt(sessionId, 'sua_chave_secreta').toString();
    return encrypted;
  };

  const displayPassword = () => {
    if (password.length === 0) return <p>Carregando senha...</p>;

    return (
      <p>
        {password.map(pair => `[${pair[0]},${pair[1]}]`).join(' ')}
      </p>
    );
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
          {displayPassword()}

          <h2>Clique nos botões abaixo para digitar a senha:</h2>
          {displayButtons()}

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
