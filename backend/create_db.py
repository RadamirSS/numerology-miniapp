from app.db import Base, engine
from app import models

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
