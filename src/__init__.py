import uuid
from datetime import datetime
import trino
from .settings import DB_HOST, DB_PORT


ENGINE_ID = str(uuid.uuid4().hex) + "_" + str(datetime.now().strftime("%s"))


connect_db = trino.dbapi.connect(host=DB_HOST, port=DB_PORT, user="admin")
# class connect_db:
#     def __enter__(self):
#         self.conn = None
#         try:
#             self.conn = trino.dbapi.connect(host=DB_HOST, port=DB_PORT, user="admin")
#             logger.info("Resurface DB connected succesfully.")

#         except Exception as e:
#             logger.error("There was an error in DB connection.")
#             logger.debug(e)
#         return self.conn

#     def __exit__(self, type, value, traceback):
#         self.conn.close()
