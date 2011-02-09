# upgrading from db version 3 to 4

# Changes:
#
# * Appends to new rows to the 'storage' table that is needed by the new
#   storgaemonitor extension. This is actually backwards compatible.

def run(cursor):
	cursor.execute ("ALTER TABLE storage ADD COLUMN icon VARCHAR")
	cursor.execute ("ALTER TABLE storage ADD COLUMN display_name VARCHAR")
	cursor.connection.commit()

