from sqlalchemy import Column, Integer, String
from database import Base

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    image_name = Column(String)