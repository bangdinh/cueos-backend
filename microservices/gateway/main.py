import os
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "auth": os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:8001"),
    "customer": os.environ.get("CUSTOMER_SERVICE_URL", "http://127.0.0.1:8007"),
    "customers": os.environ.get("CUSTOMER_SERVICE_URL", "http://127.0.0.1:8007"),
    "permissions": os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:8001"),
    "stores": os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:8001"),
    "products": os.environ.get("INVENTORY_SERVICE_URL", "http://127.0.0.1:8002"),
    "tables": os.environ.get("INVENTORY_SERVICE_URL", "http://127.0.0.1:8002"),
    "session": os.environ.get("SESSION_SERVICE_URL", "http://127.0.0.1:8006"),
    "reports": os.environ.get("BILLING_SERVICE_URL", "http://127.0.0.1:8003"),
    "history": os.environ.get("SESSION_SERVICE_URL", "http://127.0.0.1:8006"),
    "customer-order": os.environ.get("BILLING_SERVICE_URL", "http://127.0.0.1:8003"),
    "client-notify": os.environ.get("BILLING_SERVICE_URL", "http://127.0.0.1:8003"),
    "client-poll": os.environ.get("BILLING_SERVICE_URL", "http://127.0.0.1:8003"),
    "poll": os.environ.get("BILLING_SERVICE_URL", "http://127.0.0.1:8003")
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def gateway(request: Request, path: str):
    # Path is something like 'api/auth/login'
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api":
        service_name = parts[1]
        target_url = None
        
        # Specific routing for order service (port 8005)
        if service_name == "session" and len(parts) > 2 and parts[2] in ("add-item", "add-items", "item"):
            target_url = f"{os.environ.get('ORDER_SERVICE_URL', 'http://127.0.0.1:8005')}/{path}"
        elif service_name == "customer-order":
            target_url = f"{os.environ.get('ORDER_SERVICE_URL', 'http://127.0.0.1:8005')}/{path}"
        elif service_name in SERVICES:
            target_url = f"{SERVICES[service_name]}/{path}"
            
        if target_url:
            if request.url.query:
                target_url += f"?{request.url.query}"
            
            async with httpx.AsyncClient() as client:
                body = await request.body()
                headers = dict(request.headers)
                headers.pop("host", None) # Remove host header to avoid conflicts
                
                try:
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        content=body,
                        timeout=10.0
                    )
                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                except httpx.RequestError as e:
                    raise HTTPException(status_code=503, detail=f"Service Unavailable: {str(e)}")
                    
    # If no service matches or not /api/...
    raise HTTPException(status_code=404, detail="Not Found in API Gateway")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
