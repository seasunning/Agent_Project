from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.models import User, Book, BorrowRecord, Reminder
from ..schemas.schemas import (
    UserCreate, UserLogin, UserResponse,
    BookCreate, BookResponse, BookUpdate,
    BorrowRequest, BorrowResponse, ReturnRequest,
    StatisticsResponse
)
from ..services.auth import get_current_user, create_access_token, verify_password, hash_password
from ..services.book_service import (
    create_book, get_books, get_book_by_id, update_book,
    delete_book, search_books
)
from ..services.borrow_service import (
    borrow_book, return_book, get_user_borrow_records,
    get_overdue_records
)
from ..services.statistics_service import (
    get_borrow_statistics, get_popular_books,
    get_user_borrow_history
)

router = APIRouter()

# 用户认证路由
@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册API
    """
    # 检查用户是否已存在
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.student_id == user_data.student_id)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or student ID already registered"
        )
    
    # 创建新用户
    hashed_password = hash_password(user_data.password)
    new_user = User(
        student_id=user_data.student_id,
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        role="student",
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/auth/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录API
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


# 图书管理路由
@router.get("/books", response_model=List[BookResponse])
async def get_books_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    title: Optional[str] = None,
    author: Optional[str] = None,
    isbn: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    查询图书列表API
    """
    return get_books(db, skip=skip, limit=limit, title=title, author=author, isbn=isbn)


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    获取图书详情API
    """
    book = get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book


@router.post("/admin/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_new_book(
    book_data: BookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员录入图书API
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can add books"
        )
    
    return create_book(db, book_data)


@router.put("/admin/books/{book_id}", response_model=BookResponse)
async def update_book_info(
    book_id: int,
    book_data: BookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员更新图书信息API
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update books"
        )
    
    book = update_book(db, book_id, book_data)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book


@router.delete("/admin/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_info(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员删除图书API
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete books"
        )
    
    success = delete_book(db, book_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )


# 借阅管理路由
@router.post("/borrow", response_model=BorrowResponse, status_code=status.HTTP_201_CREATED)
async def borrow_a_book(
    borrow_request: BorrowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    借阅图书API
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can borrow books"
        )
    
    return borrow_book(db, current_user.id, borrow_request.book_id)


@router.post("/return", response_model=BorrowResponse)
async def return_a_book(
    return_request: ReturnRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    归还图书API
    """
    return return_book(db, current_user.id, return_request.borrow_record_id)


@router.get("/borrow/records", response_model=List[BorrowResponse])
async def get_my_borrow_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户借阅记录API
    """
    return get_user_borrow_records(db, current_user.id)


# 统计分析路由
@router.get("/admin/statistics", response_model=StatisticsResponse)
async def get_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取借阅统计API
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view statistics"
        )
    
    # 设置默认日期范围（最近30天）
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    statistics = get_borrow_statistics(db, start_date, end_date)
    popular_books = get_popular_books(db, start_date, end_date, limit=10)
    
    return StatisticsResponse(
        total_borrows=statistics["total_borrows"],
        total_returns=statistics["total_returns"],
        active_borrows=statistics["active_borrows"],
        overdue_borrows=statistics["overdue_borrows"],
        popular_books=popular_books,
        period_start=start_date,
        period_end=end_date
    )


@router.get("/admin/overdue")
async def get_overdue_borrows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取超期借阅记录API
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view overdue records"
        )
    
    return get_overdue_records(db)


# 搜索路由
@router.get("/search/books")
async def search_books_by_keyword(
    keyword: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    搜索图书API
    """
    return search_books(db, keyword, skip=skip, limit=limit)
