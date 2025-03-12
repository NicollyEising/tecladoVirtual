const path = require('path');

module.exports = function(proxy, allowedHost) {
  return {
    static: {
      directory: path.join(__dirname, 'public'), // Diretório dos arquivos estáticos
    },
    devMiddleware: {
      publicPath: '/', // Caminho público para os arquivos de desenvolvimento
    },
    hot: true, // Habilitar hot reloading
    open: false, // Evita abrir automaticamente o navegador várias vezes
    port: 8080, // Porta do servidor
    historyApiFallback: true, // Redirecionar as requisições para o index.html
    proxy: proxy, // Configuração de proxy, se necessário
    allowedHosts: allowedHost ? 'all' : undefined, // Configuração dos hosts permitidos
  };
};
