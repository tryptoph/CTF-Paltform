import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from io import BytesIO

import dataset
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.sql import sqltypes

from CTFd import create_app
from CTFd.utils import get_app_config, string_types
from CTFd.utils.exports.freeze import freeze_export
from CTFd.utils.migrations import get_current_revision
from CTFd.models import get_class_by_tablename

def fixed_export_ctf():
    app = create_app()
    with app.app_context():
        # Get database URI
        db_uri = get_app_config("SQLALCHEMY_DATABASE_URI")
        db = dataset.connect(db_uri)

        # Backup database
        backup = tempfile.NamedTemporaryFile()
        backup_zip = zipfile.ZipFile(backup, "w")

        # Get database engine to check if tables exist
        engine = create_engine(db_uri)
        inspector = inspect(engine)

        # Get actual tables that exist in the database
        actual_tables = set(inspector.get_table_names())
        
        # Get tables from dataset (which sometimes includes non-existent tables)
        dataset_tables = set(db.tables)
        
        # Only export tables that actually exist
        tables = [table for table in dataset_tables if table in actual_tables]
        
        # Just to be safe, let's explicitly exclude desktop_container which is causing issues
        tables = [table for table in tables if table != 'desktop_container']

        # Export each table
        for table in tables:
            try:
                result = db[table].all()
                result_file = BytesIO()
                freeze_export(result, fileobj=result_file)
                result_file.seek(0)
                backup_zip.writestr("db/{}.json".format(table), result_file.read())
                print(f"Exported table {table}")
            except Exception as e:
                print(f"Error exporting table {table}: {str(e)}")
                # Create an empty table export to maintain structure
                result = {"count": 0, "results": [], "meta": {}}
                result_file = BytesIO()
                json.dump(result, result_file)
                result_file.seek(0)
                backup_zip.writestr("db/{}.json".format(table), result_file.read())

        # Guarantee that alembic_version is saved into the export
        if "alembic_version" not in tables:
            result = {
                "count": 1,
                "results": [{"version_num": get_current_revision()}],
                "meta": {},
            }
            result_file = BytesIO()
            json.dump(result, result_file)
            result_file.seek(0)
            backup_zip.writestr("db/alembic_version.json", result_file.read())

        # Backup uploads
        from CTFd.utils.uploads import get_uploader
        uploader = get_uploader()
        uploader.sync()

        upload_folder = os.path.join(
            os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
        )
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                parent_dir = os.path.basename(root)
                backup_zip.write(
                    os.path.join(root, file),
                    arcname=os.path.join("uploads", parent_dir, file),
                )

        backup_zip.close()
        backup.seek(0)
        return backup

if __name__ == "__main__":
    backup = fixed_export_ctf()
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], "wb") as target:
            shutil.copyfileobj(backup, target)
    else:
        from CTFd.utils import config
        ctf_name = config.ctf_name()
        day = datetime.datetime.now().strftime("%Y-%m-%d")
        full_name = "{}.{}.zip".format(ctf_name, day)

        with open(full_name, "wb") as target:
            shutil.copyfileobj(backup, target)

        print("Exported {filename}".format(filename=full_name))
