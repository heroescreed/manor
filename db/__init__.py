from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///db/database.db', echo=True)
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    return Session()