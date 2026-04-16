from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.app.core.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    borrow_records = relationship("BorrowRecord", back_populates="user")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(13), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    publisher = Column(String(100))
    publication_year = Column(Integer)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    location = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    borrow_records = relationship("BorrowRecord", back_populates="book")


class BorrowStatus(str, enum.Enum):
    BORROWED = "borrowed"
    RETURNED = "returned"
    OVERDUE = "overdue"


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrow_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    return_date = Column(DateTime(timezone=True))
    status = Column(Enum(BorrowStatus), default=BorrowStatus.BORROWED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="borrow_records")
    book = relationship("Book", back_populates="borrow_records")
    reminders = relationship("Reminder", back_populates="borrow_record")


class ReminderType(str, enum.Enum):
    UPCOMING_DUE = "upcoming_due"
    OVERDUE = "overdue"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    borrow_record_id = Column(Integer, ForeignKey("borrow_records.id"), nullable=False)
    reminder_type = Column(Enum(ReminderType), nullable=False)
    reminder_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    borrow_record = relationship("BorrowRecord", back_populates="reminders")