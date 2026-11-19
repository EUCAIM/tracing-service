#!/bin/sh

while getopts "h:p:a:s:u:d:m:" opt; do
  case "$opt" in
    h) HOST="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    a) ADMIN="$OPTARG" ;;
    m) ADMIN_PASSWORD="$OPTARG" ;;
    u) USER="$OPTARG" ;;
    s) USER_PASSWORD="$OPTARG" ;;
    d) DB_NAME="$OPTARG" ;;
    *) echo "Invalid option"; exit 1 ;;
  esac
done

shift $((OPTIND - 1))  # Remove parsed options from $@

if [ -z "$HOST" ] || [ -z "$PORT" ] || [ -z "$ADMIN" ] || [ -z "$ADMIN_PASSWORD" ] || [ -z "$USER" ] || [ -z "$USER_PASSWORD" ] || [ -z "$DB_NAME" ]; then
  echo "Error: All of -h (Tracing DB host), -p (Tracing DB port), -a (Tracing DB admin name), -m (Tracing DB admin password), -u (user for the tracing app), -d (the name of the database used for tracing), and -s (password of the user for the tracing app) are required" >&2
  exit 1
fi

DEFAULT_DB=defaultdb
script_dir=$(cd "$(dirname "$0")" && pwd)
SQL_SCRIPT="${script_dir}/v2.sql"

# PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN  -d $DB_NAME -c '\dt'
# echo $?
echo "Attempting connection to DB $DB_NAME"
DB_EXEC="$(PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c '\dt' 2>&1)"
DB_EXEC_CODE=$?
# echo $DB_EXEC $DB_EXEC_CODE


if [ $DB_EXEC_CODE -ne 0 ]; then

    if echo "$DB_EXEC" | grep -q "selected db doesn't exist"; then
        echo "DB $DB_NAME not found... creating..."
        PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -c "CREATE DATABASE $DB_NAME;"
    else

        echo "An error has occured when trying to connect to DB $DB_NAME (wasn't able to check its existance): $DB_EXEC"
        exit $DB_EXEC_CODE
    fi
fi

echo "Attempting connection to DB $DB_NAME"


echo "Create table(s) from script $SQL_SCRIPT"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -f $SQL_SCRIPT

echo "Create app user"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c "CREATE USER $USER WITH PASSWORD '$USER_PASSWORD';"
echo "Grant SELECT, INSERT, revoke everything else"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c "GRANT CONNECT ON DATABASE $DB_NAME TO $USER;"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c "GRANT USAGE ON SCHEMA public TO $USER;"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c "GRANT DELETE ON ALL TABLES IN SCHEMA public TO $USER;"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM $USER;"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U $ADMIN -d $DB_NAME -c "GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO $USER;"
echo "Check permissions"
forbidden=$(
  PGPASSWORD="$ADMIN_PASSWORD" psql  -h $HOST -p $PORT -U $ADMIN  -X -A -t -q \
    -v ON_ERROR_STOP=1 \
    -v "target_role=$USER" \
    -v "target_schema=public" \
    -d "$DB_NAME" <<'SQL'
SELECT
    n.nspname || '.' || c.relname || ': ' || p.privilege
FROM pg_class AS c
JOIN pg_namespace AS n
  ON n.oid = c.relnamespace
CROSS JOIN (
    VALUES
        ('UPDATE'),
        ('DELETE'),
        ('TRUNCATE'),
        ('REFERENCES'),
        ('TRIGGER')
) AS p(privilege)
WHERE c.relkind IN ('r', 'p', 'v', 'm')
  AND n.nspname = :'target_schema'
  AND has_table_privilege(:'target_role', c.oid, p.privilege)
ORDER BY n.nspname, c.relname, p.privilege;
SQL
)

if [ -n "$forbidden" ]; then
    echo "FAIL: forbidden privileges found for $ROLE:"
    printf '%s\n' "$forbidden"
    exit 1
fi

echo "OK: $USER has no effective table privileges beyond SELECT and INSERT"




