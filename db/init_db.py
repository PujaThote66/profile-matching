from db.database import engine, Base
from db import models  # Important: imports all tables

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
