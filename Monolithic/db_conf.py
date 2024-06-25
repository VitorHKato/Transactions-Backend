from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URI = 'sqlite:///ecommerce.db'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

