// frontend/config/paths.js

const path = require('path');

const appDirectory = path.resolve(__dirname, '..');
const resolveApp = relativePath => path.resolve(appDirectory, relativePath);

module.exports = {
  appPath: appDirectory,
  appBuild: resolveApp('build'),
  appPublic: resolveApp('public'),
  appHtml: resolveApp('public/index.html'),
  appIndexJs: resolveApp('src/index.js'),
  appPackageJson: resolveApp('package.json'),
  appSrc: resolveApp('src'),
  appNodeModules: resolveApp('node_modules'),
  publicUrlOrPath: '/',
};
