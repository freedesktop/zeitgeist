# upgrading from db version 3 to 4

# Changes:
#
# * Appends to new rows to the 'storage' table that is needed by the new
#   storagemonitor extension. This is actually backwards compatible.

from zeitgeist.datamodel import StorageState

def run(cursor):
	# Add the new columns for the storage table
	cursor.execute ("ALTER TABLE storage ADD COLUMN icon VARCHAR")
	cursor.execute ("ALTER TABLE storage ADD COLUMN display_name VARCHAR")
	
	# Add the default storage mediums 'UNKNOWN' and 'local' and set them
	# as always available
	cursor.execute("INSERT INTO storage (value, state) VALUES ('unknown', ?)", (StorageState.Available,))
	unknown_storage_rowid = cursor.lastrowid
	cursor.execute("INSERT INTO storage (value, state) VALUES ('local', ?)", (StorageState.Available,))
	
	# Set all subjects that are already in the DB to have 'unknown' storage
	# That way they will always be marked as available. We don't have a chance
	# of properly backtracking all items, so we use this as a clutch
	cursor.execute("UPDATE event SET subj_storage=? WHERE subj_storage IS NULL", (unknown_storage_rowid, ))
	
	cursor.connection.commit()
  
