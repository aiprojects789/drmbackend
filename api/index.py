import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def handler(request):
    """
    Simple Vercel handler that provides basic API responses
    """
    try:
        # Set CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        
        # Handle preflight requests
        if request.get('method') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Get path from request
        path = request.get('path', '/')
        method = request.get('method', 'GET')
        
        # Route requests
        if path == '/':
            response_body = {
                "message": "ART_DRM Backend Service",
                "status": "running",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/",
                    "api": "/api/v1/",
                    "docs": "/docs",
                    "swagger": "/docs"
                }
            }
        elif path == '/docs':
            # Return Swagger UI HTML
            swagger_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>ART_DRM API Documentation</title>
                <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
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
            </html>
            """
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/html'},
                'body': swagger_html
            }
        elif path == '/openapi.json':
            # Return OpenAPI spec
            openapi_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "ART_DRM Backend",
                    "description": "Digital Rights Management for Artworks",
                    "version": "1.0.0"
                },
                "paths": {
                    "/": {
                        "get": {
                            "summary": "Root endpoint",
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
                                                    "version": {"type": "string"}
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
                            "responses": {
                                "200": {
                                    "description": "Available API endpoints",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(openapi_spec)
            }
        elif path.startswith('/api/v1/'):
            response_body = {
                "message": "API v1 endpoints available",
                "path": path,
                "method": method,
                "available_endpoints": [
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
            }
        else:
            response_body = {
                "message": "Endpoint not found",
                "path": path,
                "available_endpoints": ["/", "/api/v1/", "/docs", "/openapi.json"]
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        # Error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e),
                'status': 'error'
            })
        }
