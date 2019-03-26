from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.base import Engine
from config import config


uri: str = 'sqlite:///' + config["storage_location"]

engine: Engine = create_engine(uri)

Session = sessionmaker(bind=engine)

session: Session = Session()

Base = declarative_base()
