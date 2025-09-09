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
  
  if (pathname === '/') {
    const responseBody = {
      message: "ART_DRM Backend Service",
      status: "running",
      version: "1.0.0",
      endpoints: {
        health: "/",
        api: "/api/v1/",
        docs: "/docs",
        swagger: "/docs"
      }
    };
    res.status(200).json(responseBody);
  } else if (pathname === '/docs') {
    // Return Swagger UI HTML
    const swaggerHtml = `
<!DOCTYPE html>
<html>
<head>
    <title>ART_DRM API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        body { margin: 0; }
        .swagger-ui .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ]
        });
    </script>
</body>
</html>`;
    res.setHeader('Content-Type', 'text/html');
    res.status(200).send(swaggerHtml);
  } else if (pathname === '/openapi.json') {
    // Return OpenAPI spec
    const openapiSpec = {
      "openapi": "3.0.0",
      "info": {
        "title": "ART_DRM Backend",
        "description": "Digital Rights Management for Artworks",
        "version": "1.0.0",
        "contact": {
          "name": "ART_DRM Team",
          "email": "support@artdrm.com"
        }
      },
      "servers": [
        {
          "url": "https://drmbackend-1ofdfgf45-nameer-6s-projects.vercel.app",
          "description": "Production server"
        }
      ],
      "paths": {
        "/": {
          "get": {
            "summary": "Root endpoint",
            "description": "Get service status and available endpoints",
            "tags": ["Health"],
            "responses": {
              "200": {
                "description": "Service status",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "object",
                      "properties": {
                        "message": {"type": "string"},
                        "status": {"type": "string"},
                        "version": {"type": "string"},
                        "endpoints": {
                          "type": "object",
                          "properties": {
                            "health": {"type": "string"},
                            "api": {"type": "string"},
                            "docs": {"type": "string"},
                            "swagger": {"type": "string"}
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "/api/v1/": {
          "get": {
            "summary": "API v1 endpoints",
            "description": "Get list of available API v1 endpoints",
            "tags": ["API"],
            "responses": {
              "200": {
                "description": "Available API endpoints",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "object",
                      "properties": {
                        "message": {"type": "string"},
                        "path": {"type": "string"},
                        "method": {"type": "string"},
                        "available_endpoints": {
                          "type": "array",
                          "items": {"type": "string"}
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "/api/v1/auth/": {
          "get": {
            "summary": "Authentication endpoints",
            "description": "Authentication and user management",
            "tags": ["Authentication"],
            "responses": {
              "200": {
                "description": "Authentication endpoints available"
              }
            }
          }
        },
        "/api/v1/artwork/": {
          "get": {
            "summary": "Artwork management",
            "description": "Create, read, update, and delete artworks",
            "tags": ["Artwork"],
            "responses": {
              "200": {
                "description": "Artwork endpoints available"
              }
            }
          }
        },
        "/api/v1/blockchain/": {
          "get": {
            "summary": "Blockchain operations",
            "description": "Blockchain interactions and smart contract operations",
            "tags": ["Blockchain"],
            "responses": {
              "200": {
                "description": "Blockchain endpoints available"
              }
            }
          }
        },
        "/api/v1/admin/": {
          "get": {
            "summary": "Admin operations",
            "description": "Administrative functions and system management",
            "tags": ["Admin"],
            "responses": {
              "200": {
                "description": "Admin endpoints available"
              }
            }
          }
        },
        "/api/v1/contact/": {
          "get": {
            "summary": "Contact management",
            "description": "Contact form and communication endpoints",
            "tags": ["Contact"],
            "responses": {
              "200": {
                "description": "Contact endpoints available"
              }
            }
          }
        },
        "/api/v1/email/": {
          "get": {
            "summary": "Email services",
            "description": "Email sending and management",
            "tags": ["Email"],
            "responses": {
              "200": {
                "description": "Email endpoints available"
              }
            }
          }
        },
        "/api/v1/licenses/": {
          "get": {
            "summary": "License management",
            "description": "Digital license creation and management",
            "tags": ["Licenses"],
            "responses": {
              "200": {
                "description": "License endpoints available"
              }
            }
          }
        },
        "/api/v1/transactions/": {
          "get": {
            "summary": "Transaction management",
            "description": "Financial transactions and payment processing",
            "tags": ["Transactions"],
            "responses": {
              "200": {
                "description": "Transaction endpoints available"
              }
            }
          }
        },
        "/api/v1/web3/": {
          "get": {
            "summary": "Web3 integration",
            "description": "Web3 wallet and blockchain integration",
            "tags": ["Web3"],
            "responses": {
              "200": {
                "description": "Web3 endpoints available"
              }
            }
          }
        }
      },
      "tags": [
        {
          "name": "Health",
          "description": "Health check and service status"
        },
        {
          "name": "API",
          "description": "API information and discovery"
        },
        {
          "name": "Authentication",
          "description": "User authentication and authorization"
        },
        {
          "name": "Artwork",
          "description": "Digital artwork management"
        },
        {
          "name": "Blockchain",
          "description": "Blockchain and smart contract operations"
        },
        {
          "name": "Admin",
          "description": "Administrative functions"
        },
        {
          "name": "Contact",
          "description": "Contact and communication"
        },
        {
          "name": "Email",
          "description": "Email services"
        },
        {
          "name": "Licenses",
          "description": "Digital license management"
        },
        {
          "name": "Transactions",
          "description": "Financial transactions"
        },
        {
          "name": "Web3",
          "description": "Web3 integration"
        }
      ]
    };
    res.status(200).json(openapiSpec);
  } else if (pathname.startsWith('/api/v1/')) {
    const responseBody = {
      message: "API v1 endpoints available",
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
    res.status(200).json(responseBody);
  } else if (pathname === '/favicon.ico') {
    // Handle favicon requests
    res.status(204).end();
  } else {
    const responseBody = {
      message: "Endpoint not found",
      path: pathname,
      available_endpoints: ["/", "/api/v1/", "/docs", "/openapi.json"]
    };
    res.status(404).json(responseBody);
  }
};