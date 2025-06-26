from sqlalchemy import create_engine


# Instantiate SQLAlchemy engine 
engine = create_engine('postgresql+psycopg2://postgres:password@127.0.0.1:5432/bandify')