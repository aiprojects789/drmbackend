module.exports = (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  // Simple routing
  const { pathname } = new URL(req.url, `http://${req.headers.host}`);
  
  let responseBody;
  
  if (pathname === '/') {
    responseBody = {
      message: "ART_DRM Backend Service",
      status: "running",
      version: "1.0.0",
      endpoints: {
        health: "/",
        api: "/api/v1/",
        docs: "/docs"
      }
    };
  } else if (pathname.startsWith('/api/v1/')) {
    responseBody = {
      message: "API endpoints available",
      path: pathname,
      method: req.method,
      available_endpoints: [
        "/api/v1/auth/",
        "/api/v1/artwork/",
        "/api/v1/blockchain/",
        "/api/v1/admin/",
        "/api/v1/contact/",
        "/api/v1/email/",
        "/api/v1/licenses/",
        "/api/v1/transactions/",
        "/api/v1/web3/"
      ]
    };
  } else if (pathname === '/docs') {
    responseBody = {
      message: "API Documentation",
      swagger_url: "/docs",
      openapi_url: "/openapi.json"
    };
  } else {
    responseBody = {
      message: "Endpoint not found",
      path: pathname,
      available_endpoints: ["/", "/api/v1/", "/docs"]
    };
  }
  
  res.status(200).json(responseBody);
};