const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to backend
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
    })
  );

  // Proxy other backend endpoints
  app.use(
    ['/fork', '/btc', '/3commas', '/active-trades', '/health', '/docs', '/config', '/price-series', '/dca'],
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
    })
  );
};
