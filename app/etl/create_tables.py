from Database.database import Base, engine
from Database import models  # noqa: F401


Base.metadata.create_all(engine)




