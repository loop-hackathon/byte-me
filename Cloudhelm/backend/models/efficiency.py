from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.core.db import Base

class ResourceEfficiency(Base):
    __tablename__ = "resource_efficiency"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service = Column(String, index=True)
    cpu_util = Column(Float)
    cost = Column(Float)
    efficiency_score = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
