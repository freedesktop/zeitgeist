# upgrading from db version 2 to 1
# this requires no update to the actual data in the database
# it is only a schema change of event_view. This change is done
# in sql.create_db()

# the schema change is renaming 'subj_uri_id' column to 'subj_id', as
# both values are the same. Also 'subj_origin' gets renamed to
# 'subj_origin_uri' and 'subj_origin_id' to 'subj_origin'.

def run(cursor):
    pass
