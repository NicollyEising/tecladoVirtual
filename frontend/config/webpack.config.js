const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin'); // Adicionando o plugin

module.exports = (env, argv) => {
  return {
    mode: argv.mode || 'development', // Permite passar o modo como argumento

    entry: './src/index.js', // Arquivo de entrada

    output: {
      filename: '[name].[contenthash].js', // Usando [name] e [contenthash] para nomes únicos de arquivos
      path: path.resolve(__dirname, 'dist'), // Diretório de saída
      clean: true, // Limpa a pasta antes de gerar o novo arquivo
    },

    module: {
      rules: [
        {
          test: /\.jsx?$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env', '@babel/preset-react'],
            },
          },
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader'],
        },
        {
          test: /\.scss$/,
          use: ['style-loader', 'css-loader', 'sass-loader'],
        },
        {
          test: /\.(jpg|jpeg|png|gif|svg|woff|woff2|eot|ttf|otf)$/,
          type: 'asset/resource',
        },
      ],
    },

    resolve: {
      extensions: ['.js', '.jsx', '.css', '.scss'],
    },

    devServer: {
      static: {
        directory: path.join(__dirname, 'public'),
      },
      port: 8080,
      open: true,
      hot: true,
      historyApiFallback: true,
    },

    optimization: {
      splitChunks: {
        chunks: 'all',
        automaticNameDelimiter: '-', // Adiciona um delimitador para nomes de chunks
      },
    },

    plugins: [
      new HtmlWebpackPlugin({
        template: './public/index.html', // Usando o seu index.html como template
        filename: 'index.html',          // O nome do arquivo HTML gerado
      }),
    ],
  };
};
