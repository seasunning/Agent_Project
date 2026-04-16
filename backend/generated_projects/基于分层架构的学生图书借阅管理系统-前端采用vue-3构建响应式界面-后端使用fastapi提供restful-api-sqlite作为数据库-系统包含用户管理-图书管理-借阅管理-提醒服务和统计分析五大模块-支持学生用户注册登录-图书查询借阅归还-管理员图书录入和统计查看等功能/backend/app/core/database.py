from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite数据库连接URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"

# 创建数据库引擎
# connect_args参数仅用于SQLite，确保线程安全
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True  # 设置为True可在控制台查看SQL语句，生产环境应设为False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类，所有模型类将继承此类
Base = declarative_base()


def get_db():
    """
    数据库会话依赖注入函数
    为每个请求提供独立的数据库会话，请求结束后自动关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    创建所有数据库表
    应在应用启动时调用此函数
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    删除所有数据库表
    仅用于开发和测试环境
    """
    Base.metadata.drop_all(bind=engine)
