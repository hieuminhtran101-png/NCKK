from fastapi import FastAPI,HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables từ .env file
load_dotenv()

# Khởi tạo bộ lập lịch
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.db.mongodb import connect_db, disconnect_db
from app.core.redis import connect_redis, disconnect_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng."""
    # Khởi tạo Redis
    try:
        connect_redis()
    except Exception as e:
        print(f"⚠️  Warning: Redis not available: {e}")
    
    # Khởi tạo MongoDB
    try:
        await connect_db()
    except Exception as e:
        print(f"⚠️  Warning: MongoDB not available, running in fallback mode: {e}")
    
    # Khởi tạo khi ứng dụng khởi động
    init_scheduler()
    yield
    # Tắt khi ứng dụng dừng
    shutdown_scheduler()
    
    # Ngắt MongoDB
    await disconnect_db()
    
    # Ngắt Redis
    disconnect_redis()

app = FastAPI(
    title='Tôi đang học FastAPI',
    description='Các API test của tôi',
    version='1.0.0',
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Health check
@app.get('/health')
def health():
    return {'status': 'ok'}

# Register routers (imports after app initialization)
from app.api.endpoints.agent import router as agent_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.events import router as events_router
from app.api.endpoints.telegram import router as telegram_router
from app.api.endpoints.schedules import router as schedules_router
from app.api.endpoints.public_events import router as public_events_router
from app.api.endpoints.upload import router as upload_router
from app.api.endpoints.chat import router as chat_router

app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(events_router)
app.include_router(telegram_router)
app.include_router(schedules_router)
app.include_router(public_events_router)
app.include_router(upload_router)


class LoginRequest(BaseModel):
    username : str
    password : str

@app.get('/')
def read_root():
    return{'mess':'Đây là Api đầu tiên của tôi'}

@app.get('/hello')
def hello(name : str):
    return{f'chào {name} nha'}

class Info(BaseModel):
    name : str
    ngyeu : str
    trinhdo : str
    tuoi : float
    
@app.post("/info")
def info_nguoi(info : Info):
    return{
        'mess':'Tạo thành công rồi',
        'data':'info'
    }
@app.post('/login')
def login(data : LoginRequest):
    if data.username != 'Hieu':
        raise HTTPException(
            status_code= 401,
            detail= "sai ten dang nhap thang ngu"
        )
    return {'mess': 'dang nhap thang cong roi'}