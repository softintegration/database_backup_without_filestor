# -*- coding: utf-8 -*-
import json
import logging
import os
import shutil
import tempfile

import odoo
import odoo.release
import odoo.sql_db
import odoo.tools

# here we have to minimize the duplication of helpers method to reduce the module upgrading risks
from odoo.service.db import check_db_management_enabled
from odoo.service.db import dump_db_manifest

_logger = logging.getLogger(__name__)


@check_db_management_enabled
def dump_db(db_name, stream, backup_format='zip'):
    """Dump database `db` into file-like object `stream` if stream is None
    return a file object with the dump """

    _logger.info('DUMP DB: %s format %s', db_name, backup_format)

    cmd = ['pg_dump', '--no-owner']
    cmd.append(db_name)

    if backup_format in ('zip','zip_without_filestore'):
        with tempfile.TemporaryDirectory() as dump_dir:
            if backup_format == 'zip':
                filestore = odoo.tools.config.filestore(db_name)
                if os.path.exists(filestore):
                    shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
            with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(dump_db_manifest(cr), fh, indent=4)
            cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
            odoo.tools.exec_pg_command(*cmd)
            if stream:
                odoo.tools.osutil.zip_dir(dump_dir, stream, include_dir=False,
                                          fnct_sort=lambda file_name: file_name != 'dump.sql')
            else:
                t = tempfile.TemporaryFile()
                odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False,
                                          fnct_sort=lambda file_name: file_name != 'dump.sql')
                t.seek(0)
                return t
    else:
        cmd.insert(-1, '--format=c')
        stdin, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
        if stream:
            shutil.copyfileobj(stdout, stream)
        else:
            return stdout
