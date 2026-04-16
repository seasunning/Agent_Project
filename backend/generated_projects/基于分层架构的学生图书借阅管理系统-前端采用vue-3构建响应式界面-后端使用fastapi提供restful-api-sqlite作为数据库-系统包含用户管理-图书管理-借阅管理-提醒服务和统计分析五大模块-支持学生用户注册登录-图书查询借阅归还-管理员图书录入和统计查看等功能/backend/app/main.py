from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
import uvicorn

from app.api import routers
from app.core.database import engine, get_db
from app.core.config import settings
from app.models import models

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建FastAPI应用实例
app = FastAPI(
    title="学生图书借阅管理系统 API",
    description="基于FastAPI构建的学生图书借阅管理系统后端API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2密码承载令牌方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 注册API路由
app.include_router(routers.auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(routers.books_router, prefix="/api/books", tags=["图书管理"])
app.include_router(routers.borrow_router, prefix="/api/borrow", tags=["借阅管理"])
app.include_router(routers.admin_router, prefix="/api/admin", tags=["管理员"])
app.include_router(routers.statistics_router, prefix="/api/statistics", tags=["统计分析"])

# 根路径路由
@app.get("/")
async def root():
    return {
        "message": "欢迎使用学生图书借阅管理系统API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

# 健康检查端点
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # 测试数据库连接
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"  # 实际应用中应使用datetime.now()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"数据库连接失败: {str(e)}"
        )

# API信息端点
@app.get("/api/info")
async def api_info():
    return {
        "name": "学生图书借阅管理系统",
        "version": "1.0.0",
        "description": "基于分层架构的学生图书借阅管理系统后端API",
        "author": "系统开发团队",
        "endpoints": [
            {"path": "/api/auth", "description": "用户认证相关接口"},
            {"path": "/api/books", "description": "图书管理相关接口"},
            {"path": "/api/borrow", "description": "借阅管理相关接口"},
            {"path": "/api/admin", "description": "管理员专用接口"},
            {"path": "/api/statistics", "description": "统计分析接口"}
        ]
    }

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path
        }
    }

# 启动应用
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
