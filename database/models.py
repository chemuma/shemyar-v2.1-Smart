from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    national_code = Column(String(10))
    student_id = Column(String(20))  # 44... یا 444... یا None برای مهمان
    phone = Column(String(11), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_senior_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), unique=True, nullable=False)
    type = Column(String(50))
    description = Column(Text)
    date_shamsi = Column(String(10))  # فقط 1404/09/20
    location = Column(String(200))
    cost = Column(Integer, default=0)
    capacity = Column(Integer, default=0)  # 0 = نامحدود
    remaining_capacity = Column(Integer)
    auxiliary_capacity = Column(Integer)
    status = Column(String(20), default="active")  # active, done, canceled, postponed
    hashtag = Column(String(100))
    survey_sent = Column(Boolean, default=False)

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    row_number = Column(Integer)
    payment_status = Column(String(20), default="pending")  # pending, confirmed
    registered_at = Column(DateTime, default=datetime.utcnow)

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True)
    registration_id = Column(Integer, ForeignKey("registrations.id"))
    rating = Column(Integer)  # 1-5
