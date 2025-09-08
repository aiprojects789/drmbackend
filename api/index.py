def handler(request):
    """
    Ultra-minimal Vercel handler
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': '{"message": "ART_DRM Backend Service", "status": "running", "version": "1.0.0"}'
    }