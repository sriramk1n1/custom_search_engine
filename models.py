from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import PrimaryKeyConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    email = Column(String, primary_key=True, unique=True, nullable=False)
    password = Column(String, nullable=False)
    pages = relationship("Page", back_populates="user")
    premium = Column(Boolean, default=False)

class Page(Base):
    __tablename__ = 'pages'
    pageid = Column(String, nullable=False)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False)
    email = Column(String, ForeignKey('users.email'), nullable=False)
    user = relationship("User", back_populates="pages")
    
    __table_args__ = (
        PrimaryKeyConstraint('pageid', 'email'),
    )
    
class Backwardhash(Base):
    __tablename__ = 'backwardhash'
    hash = Column(String,primary_key=True)
    url = Column(String)


DATABASE_URL = "sqlite:///./data.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
