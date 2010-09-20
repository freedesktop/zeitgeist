# upgrading from db version 1 to 2
# this requires no update to the actual data in the database
# it is only a schema change of event_view. This change is done
# in sql.create_db()

# the schema change is adding two columns 'subj_uri_id' and 'subj_origin_id'
# to the event_view

def run(cursor):
    pass
