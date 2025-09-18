import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db import database, models

print('MODULES_IMPORTED')
database.create_tables()
print('TABLES_CREATED')
