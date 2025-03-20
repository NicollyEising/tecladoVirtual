import React, { useState } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import axios from 'axios';
import 'react-toastify/dist/ReactToastify.css';
import './api.css';
import CryptoJS from 'crypto-js';

function App() {
  const [username, setUsername] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [password, setPassword] = useState({ original: [], hashed: [] });
  const [inputSequence, setInputSequence] = useState([]);
  const [token, setToken] = useState('');
  const [isSessionValid, setIsSessionValid] = useState(false);
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const [buttons, setButtons] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Função para gerar hash para cada número individualmente
  const hashToNumber = (input) => {
    if (input === undefined || input === null) {
      console.error("Valor inválido para hash:", input);
      return 0;
    }

    const hash = CryptoJS.SHA256(input.toString()).toString(CryptoJS.enc.Base64);
    let uniqueNumber = 0;
    for (let i = 0; i < hash.length; i++) {
      uniqueNumber += hash.charCodeAt(i);
    }
    // Garante que o número esteja no intervalo de 1 a 9
    return (uniqueNumber % 9) + 1;
  };

  // Função para formatar a sequência em pares
  const formatSequence = (sequence) => {
    let original = [];
    let hashed = [];
    for (let i = 0; i < sequence.length - 1; i += 2) {
      original.push([sequence[i], sequence[i + 1]]);
      hashed.push([hashToNumber(sequence[i]), hashToNumber(sequence[i + 1])]);
    }
    // Se a sequência tiver número ímpar, trata o último elemento isoladamente
    if (sequence.length % 2 !== 0) {
      const lastElement = sequence[sequence.length - 1];
      original.push([lastElement]);
      hashed.push([hashToNumber(lastElement)]);
    }
    return { original, hashed };
  };

  // Função para gerar os botões a partir da sequência
  const generateButtons = (sequence) => {
    const formatted = formatSequence(sequence);
    setPassword(formatted);
    const correctPairs = formatted.hashed;
    let allButtons = correctPairs.map(pair => ({
      shortNumber: pair[0],
      secondShortNumber: pair[1] || null, // Caso o par seja composto por um único elemento
      currentNumber: pair[0], // Inicializa o número atual com o primeiro número
    }));
    // Embaralha a ordem dos botões
    allButtons = allButtons.sort(() => Math.random() - 0.5);
    setButtons(allButtons);
  };

  // Função para gerar nova sessão
  const handleGenerateSession = async () => {
    if (!username) {
      return;
    }
    setIsLoading(true);
    try {
      const data = await generateSession(username);
      console.log('Dados recebidos da API:', data);
      if (data && data.sequence && Array.isArray(data.sequence)) {
        setSessionId(data.session_id);
        setToken(data.token);
        setIsSessionValid(true);
        generateButtons(data.sequence);
        console.log('Token de Verificação:', data.token);
        handleClearSequence();
      } else {
      }
    } catch (error) {
      console.error('Erro ao gerar sessão:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearSequence = () => {
    setInputSequence([]);  // Limpa a sequência de números digitados
  };

  // Exibe os botões misturados
  const displayButtons = () => {
    if (buttons.length === 0) return <p>Esperando sequência...</p>;
    return (
      <div className="buttons">
        {buttons.map((button, index) => (
          <button
            key={`${button.shortNumber}-${index}`}
            onClick={() => handleButtonClick(button, index)}
            disabled={isButtonDisabled}
            className="button"
          >
            {button.secondShortNumber 
              ? `${button.currentNumber} ou ${button.secondShortNumber}` 
              : button.currentNumber}
          </button>
        ))}
        {/* Botão para apagar a sequência */}
        <a
          onClick={handleClearSequence}
          className="button-clear"
        >
          <i className='bx bxs-trash'></i>
        </a>
      </div>
    );
  };

  // Função para lidar com o clique nos botões
  const handleButtonClick = (button, index) => {
    const flatPassword = Array.isArray(password.hashed) ? password.hashed.flat() : [];
    const nextExpectedNumber = flatPassword[inputSequence.length];
  
    if (nextExpectedNumber === undefined) {
      return;
    }
  
    let selectedNumber = null;
    if (button.currentNumber === nextExpectedNumber) {
      selectedNumber = button.currentNumber;
    } else if (button.secondShortNumber === nextExpectedNumber) {
      selectedNumber = button.secondShortNumber;
    }
  
    if (selectedNumber !== null) {
      setInputSequence((prevSequence) => {
        const newSequence = [...prevSequence, selectedNumber];
        console.log('Sequência do usuário após clique:', newSequence);
        if (newSequence.length === flatPassword.length) {
          const isCorrect = newSequence.every((num, index) => num === flatPassword[index]);
          if (isCorrect) {
          } else {
            setIsButtonDisabled(true);
            setTimeout(() => setIsButtonDisabled(false), 2000);
          }
        }
        // Embaralha os botões após o clique
        generateButtons(password.original.flat());
        return newSequence;
      });
    } else {
      setIsButtonDisabled(true);
      setTimeout(() => setIsButtonDisabled(false), 2000);
    }

    // Alterna o número mostrado no botão após cada clique
    setButtons((prevButtons) => {
      const newButtons = [...prevButtons];
      const updatedButton = { ...newButtons[index] };
      updatedButton.currentNumber = updatedButton.currentNumber === updatedButton.shortNumber 
        ? updatedButton.secondShortNumber 
        : updatedButton.shortNumber;
      newButtons[index] = updatedButton;
      return newButtons;
    });
  };

  // Exibe a senha gerada (versão hasheada)
  const displayGeneratedPassword = () => {
    if (!password.original || password.original.length === 0) return <p>Esperando sequência...</p>;
    const generatedPassword = password.hashed.flat();  // Flatten the hashed array
    return (
      <div>
        <h2 className="senha-gerada">Senha Gerada:</h2>
        <p className='senha'>{generatedPassword.join('')}</p> {/* Agora como string contínua */}
      </div>
    );
  };

  // Função para validar a sequência digitada pelo usuário
  const handleValidatePassword = async () => {
    try {
      console.log('Session ID enviado:', sessionId);
      const flatPassword = password.hashed.flat();
      if (inputSequence.join(' ') !== flatPassword.join(' ')) {
        return;
      }
      const data = {
        session_id: sessionId,
        sequence: password.original.flat(),
      };
      const encryptedSessionId = CryptoJS.AES.encrypt(sessionId, 'chave-secreta').toString();
      const response = await axios.post('http://127.0.0.1:8000/validate_sequence', data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Encrypted-Session-Id': encryptedSessionId,
        },
      });
      console.log('✅ Sequência validada com sucesso:', response.data);
      setIsSessionValid(false);
    } catch (error) {
      console.log('Error response:', error.response ? error.response.data : error.message);
    }
  };

  // Função para gerar sessão no backend
  const generateSession = async (username) => {
    const response = await axios.post('http://127.0.0.1:8000/generate_session', { username });
    console.log('Resposta da API de geração de sessão:', response.data);
    return response.data;
  };

  return (
    <div className="App wrapper">
      <h1>Teclado Virtual</h1>
      {!isSessionValid ? (
        <>
          <div className="form-container">
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Nome de usuário"
            />
            <i className="bx bxs-user"></i>
          </div>
          <button onClick={handleGenerateSession} className="primary-button" disabled={isLoading}>
            {isLoading ? 'Gerando Sessão...' : 'Gerar Nova Sessão'}
          </button>
        </>
      ) : (
        <>
          {displayGeneratedPassword()}
          <h2 className='clique'>Clique nos botões abaixo para digitar a senha:</h2>
          <div className="buttons-container">{displayButtons()}</div>
          <h3>Senha Selecionada:</h3>
          <p className='senha-digitada'>{inputSequence.join(' ')}</p>
          <button onClick={handleValidatePassword} className="primary-button .validar-senha">
            Validar Senha
          </button>
        </>
      )}
      <ToastContainer />
    </div>
  );
}

export default App;
