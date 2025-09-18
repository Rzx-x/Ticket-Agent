import sys
sys.path.append(r'c:\Users\lenovo\Documents\GitHub\Ticket-Agent')
from db import database, models
print('MODULES_IMPORTED')
database.create_tables()
print('TABLES_CREATED')
