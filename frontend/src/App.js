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
    return (uniqueNumber % 9) + 1;
  };

  const formatSequence = (sequence) => {
    let original = [];
    let hashed = [];
    for (let i = 0; i < sequence.length - 1; i += 2) {
      original.push([sequence[i], sequence[i + 1]]);
      hashed.push([hashToNumber(sequence[i]), hashToNumber(sequence[i + 1])]);
    }
    if (sequence.length % 2 !== 0) {
      const lastElement = sequence[sequence.length - 1];
      original.push([lastElement]);
      hashed.push([hashToNumber(lastElement)]);
    }
    return { original, hashed };
  };

  const generateButtons = (sequence) => {
  const formatted = formatSequence(sequence);
  setPassword(formatted);

  // Gera os pares corretos da sequência formatada
  const correctPairs = formatted.hashed;
  let allButtons = [];

  // Cria os pares de números
  for (let i = 0; i < correctPairs.length; i++) {
    if (correctPairs[i].length === 2) {
      // Se o par já for completo, adiciona diretamente
      allButtons.push({
        shortNumber: correctPairs[i][0],
        secondShortNumber: correctPairs[i][1],
      });
    } else {
      // Caso o par tenha apenas um número, gera um número aleatório para emparelhar
      const randomPairNumber = Math.floor(Math.random() * 9) + 1;  // Gera um número aleatório de 1 a 9
      allButtons.push({
        shortNumber: correctPairs[i][0],
        secondShortNumber: randomPairNumber,  // Emparelha com o número aleatório
      });
    }
  }

  // Embaralha a ordem dos botões
  allButtons = allButtons.sort(() => Math.random() - 0.5);

  // Atualiza o estado com os botões gerados
  setButtons(allButtons);
};


  const handleClearInput = () => {
    setInputSequence([]);
  };

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
        handleClearSequence();
        console.log('Token de Verificação:', data.token);
      } else {
      }
    } catch (error) {
      console.error('Erro ao gerar sessão:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const displayButtons = () => {
    if (buttons.length === 0) return <p>Esperando sequência...</p>;
    return (
      <div className="buttons">
        {buttons.map((button, index) => (
          <button
            key={`${button.shortNumber}-${index}`}
            onClick={() => handleButtonClick(button.shortNumber, button.secondShortNumber)}
            disabled={isButtonDisabled}
            className="button"
          >
            {button.secondShortNumber
              ? `${button.shortNumber} ou ${button.secondShortNumber}`
              : button.shortNumber}
          </button>
        ))}
      </div>
    );
  };

const handleButtonClick = (shortNumber, secondShortNumber) => {
  const flatPassword = Array.isArray(password.hashed) ? password.hashed.flat() : [];
  const nextExpectedNumber = flatPassword[inputSequence.length];

  if (nextExpectedNumber === undefined) {
    return;
  }

  let selectedNumber = null;
  if (shortNumber === nextExpectedNumber) {
    selectedNumber = shortNumber;
  } else if (secondShortNumber === nextExpectedNumber) {
    selectedNumber = secondShortNumber;
  } else {
    // Se nenhum for o correto, adiciona um deles aleatoriamente
    selectedNumber = Math.random() < 0.5 ? shortNumber : secondShortNumber;
  }

  setInputSequence((prevSequence) => {
    const newSequence = [...prevSequence, selectedNumber];
    console.log('Sequência do usuário após clique:', newSequence);
    
    if (newSequence.length === flatPassword.length) {
      const isCorrect = newSequence.every((num, index) => num === flatPassword[index]);
      if (!isCorrect) {
        setIsButtonDisabled(true);
        setTimeout(() => setIsButtonDisabled(false), 2000);
      }
    }

    generateButtons(password.original.flat());
    return newSequence;
  });
};


  

  const handleClearSequence = () => {
    setInputSequence([]);  // Limpa a sequência de números digitados
  };
  const displayGeneratedPassword = () => {
    if (!password.original || password.original.length === 0) return <p>Esperando sequência...</p>;
  
    const generatedPassword = password.hashed.flat();  
    return (
      <div>
        <h2 className="senha-gerada">Senha Gerada:</h2>
        <p className='senha'>{generatedPassword.join('')}</p> {}
      </div>
    );
  };

  const handleValidatePassword = async () => {
    try {
      console.log('Session ID enviado:', sessionId);
      const flatPassword = password.hashed.flat();
      
      // Verificar se a sequência de entrada é diferente da senha esperada
      if (inputSequence.join(' ') !== flatPassword.join(' ')) {
        // Enviar a senha errada para o backend
        const errorData = {
          session_id: sessionId,
          attempted_sequence: inputSequence.join(' '),  // Senha errada
        };
        const encryptedSessionId = CryptoJS.AES.encrypt(sessionId, 'chave-secreta').toString();

        // Enviar a senha errada usando axios
        const response = await axios.post('http://127.0.0.1:8000/validate_sequence', errorData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Encrypted-Session-Id': encryptedSessionId,
          },
        });
        
        // Caso a senha errada tenha sido processada no backend, logar a resposta
        console.log('Senha errada enviada:', response.data);
        return; // Evitar continuar a execução após erro
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
          <div className="clear-button">
            <button onClick={handleClearInput} className="secondary-button">
              <i className='bx bxs-eraser apagar'></i>
            </button>
          </div>
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
