from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import config

uri = 'mysql://'+config["MYSQL_USERNAME"] + ":" + str(config["MYSQL_PASSWORD"]) + '@' + str(config["MYSQL_HOSTNAME"]) \
      + ":" + str(config["MYSQL_PORT"]) + "/" + str(config["MYSQL_DATABASE"])

engine = create_engine(uri)
Session = sessionmaker(bind=engine)

session: Session = Session()

Base = declarative_base()