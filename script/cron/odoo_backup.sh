#!/bin/bash
ODOO_DATABASE=$1
echo "Backing up database: ${ODOO_DATABASE}"

BACKUP_DIR=/backup/${ODOO_DATABASE}
TMP_DUMP=/tmp/${ODOO_DATABASE}.dump
BACK_TGZ=${BACKUP_DIR}/archive.$(date +%F).tgz

# create a backup directory
echo "Prepared folder: ${BACKUP_DIR}"
mkdir -p ${BACKUP_DIR}

# Dump PG Database:
echo "DUMP command:  pg_dump -Fc -f ${TMP_DUMP} ${ODOO_DATABASE}"
pg_dump -Fc -f ${TMP_DUMP} ${ODOO_DATABASE}

# Compress DB and DB folder:
echo "TAR Command: tar cjf ${BACK_TGZ} ${TMP_DUMP} ~/.local/share/Odoo/filestore/${ODOO_DATABASE}"
tar cjf ${BACK_TGZ} ${TMP_DUMP} ~/.local/share/Odoo/filestore/${ODOO_DATABASE}

# delete old backups
echo "Clean command: find ${BACKUP_DIR} -type f -mtime +7 -name \"archive.*.tgz\" -delete"
find ${BACKUP_DIR} -type f -mtime +7 -name "archive.*.tgz" -delete







