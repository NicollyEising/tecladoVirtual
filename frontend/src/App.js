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

  // Função para validar a seleção
  const isValidSelection = (selectedNumber) => {
    const flatPassword = password.flat();  // Aqui "achata" a sequência correta da senha
    const nextExpectedNumber = flatPassword[inputSequence.length];  // Verifica o próximo número esperado
    return selectedNumber === nextExpectedNumber;
  };

  // Função para lidar com o clique nos botões
  const handleButtonClick = (pair) => {
    const flatPassword = password.flat(); // "Achata" a senha para facilitar a comparação
    const nextExpectedNumber = flatPassword[inputSequence.length]; // Obtém o próximo número esperado da senha
    
    // Verifica se o número do par é válido (igual ao próximo número esperado)
    const isValid = pair.includes(nextExpectedNumber); // Verifica se o próximo número esperado está no par

    if (isValid) {
      // Se for válido, adiciona o número à sequência
      setInputSequence((prevSequence) => {
        const newSequence = [...prevSequence, nextExpectedNumber];
        console.log("Sequência do usuário após clique:", newSequence);
        return newSequence;
      });
    } else {
      // Se for inválido, exibe uma mensagem de erro e não faz nada
      toast.error(`Número ${nextExpectedNumber} não está no par. Tente novamente.`);
    }
  };

  // Gera botões misturados, incluindo as alternativas corretas
  const generateButtons = (sequence) => {
    let correctPairs = [];
    
    // Criar pares corretos com opções alternativas
    for (let i = 0; i < sequence.length; i += 2) {
      let num1 = sequence[i];
      let num2 = sequence[i + 1];
      
      // Adiciona cada par como uma opção alternada
      correctPairs.push([num1, num2]);
    }

    let allButtons = [];

    // Adiciona os pares corretos
    correctPairs.forEach(pair => {
      allButtons.push(pair);
    });

    // Adiciona pares falsos aleatórios
    for (let i = 0; i < correctPairs.length; i++) {
      let num1 = Math.floor(Math.random() * 10);  // Número aleatório entre 0-9
      let num2 = Math.floor(Math.random() * 10);
      allButtons.push([num1, num2]);
    }

    // Embaralha os pares de botões
    allButtons = allButtons.sort(() => Math.random() - 0.5);

    // Define os botões embaralhados no estado
    setButtons(allButtons);
  };

  // Exibe os botões misturados
  const displayButtons = () => {
    if (buttons.length === 0) return <p>Esperando sequência...</p>;

    return (
      <div className="buttons">
        {buttons.map((pair, index) => (
          <button
            key={index}
            onClick={() => handleButtonClick(pair)}  // Passa o par inteiro para a função de clique
            disabled={isButtonDisabled}
          >
            [{pair[0]} ou {pair[1]}]
          </button>
        ))}
      </div>
    );
  };

  // Função para validar a sequência ao final
  const handleValidatePassword = async () => {
    try {
      // Ensure the sequence is in pairs
      const formattedSequence = [];
      for (let i = 0; i < inputSequence.length; i += 2) {
        formattedSequence.push([inputSequence[i], inputSequence[i + 1]]);
      }
  
      console.log("Senha do usuário antes do envio:", formattedSequence);
  
      // Check if the formatted sequence matches the password
      const isSequenceCorrect = formattedSequence.every((pair, index) => {
        return (
          pair[0] === password[index][0] && pair[1] === password[index][1]
        );
      });
  
      if (!isSequenceCorrect) {
        toast.error('Sequência incorreta');
        return;
      }
  
      const response = await axios.post('http://127.0.0.1:8000/validate_sequence', {
        withCredentials: true,
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
  
  // Função para gerar sessão no backend
  const generateSession = async (username) => {
    const response = await axios.post('http://127.0.0.1:8000/generate_session', { username });
    console.log('Resposta da API de geração de sessão:', response.data);
    return response.data;
  };

  // Exibe a senha gerada de forma formatada
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
