// frontend/config/env.js
const fs = require('fs');
const path = require('path');

// Carrega as variáveis de ambiente do arquivo .env, se disponível
const dotenv = require('dotenv');
const dotenvFiles = [
  path.join(process.cwd(), '.env'),
  path.join(process.cwd(), '.env.development'),
  path.join(process.cwd(), '.env.development.local'),
];

dotenvFiles.forEach(dotenvFile => {
  if (fs.existsSync(dotenvFile)) {
    dotenv.config({ path: dotenvFile });
  }
});

// Retorna o objeto com as variáveis de ambiente
function getClientEnvironment(publicUrl) {
  const raw = Object.keys(process.env)
    .filter(key => key.startsWith('REACT_APP_'))
    .reduce((env, key) => {
      env[key] = process.env[key];
      return env;
    }, {});

  // Permite que as variáveis de ambiente do projeto sejam acessíveis
  return {
    raw,
    publicUrl,
  };
}

module.exports = getClientEnvironment;
