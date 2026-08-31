#!/bin/sh

while getopts "h:p:a:s:u:" opt; do
  case "$opt" in
    h) HOST="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    a) ADMIN_PASSWORD="$OPTARG" ;;
    u) USER="$OPTARG" ;;
    s) USER_PASSWORD="$OPTARG" ;;
    d) DB_NAME="$OPTARG" ;;
    *) echo "Invalid option"; exit 1 ;;
  esac
done

shift $((OPTIND - 1))  # Remove parsed options from $@

if [ -z "$HOST" ] || [ -z "$PORT" ] || [ -z "$ADMIN_PASSWORD" ] || [ -z "$USER" ] || [ -z "$USER_PASSWORD" ] || [ -z "$DB_NAME" ]; then
  echo "Error: All of -h (ImmuDB host), -p (ImmuDB port), -a (immudb admin password), -u (user for the tracing app), -d (the name of the database used for tracing), and -s (password of the user for the tracing app) are required" >&2
  exit 1
fi

DEFAULT_DB=defaultdb
SQL_SCRIPT="./v2.sql"

# PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c '\dt'
# echo $?
echo "Attempting connection to DB $DB_NAME"
DB_EXEC="$(PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c '\dt' 2>&1)"
DB_EXEC_CODE=$?
# echo $DB_EXEC $DB_EXEC_CODE


if [ $DB_EXEC_CODE -ne 0 ]; then

    if echo "$DB_EXEC" | grep -q "selected db doesn't exist"; then
        echo "DB $DB_NAME not found... creating..."
        PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DEFAULT_DB -c "CREATE DATABASE $DB_NAME;"
    else

        echo "An error has occured when trying to connect to DB $DB_NAME (wasn't able to check its existance): $DB_EXEC"
        exit $DB_EXEC_CODE
    fi
fi

echo "Attempting connection to DB $DB_NAME"


echo "Create table(s) from script $SQL_SCRIPT"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -f $SQL_SCRIPT

echo "Create app user"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "CREATE USER $USER WITH PASSWORD '$USER_PASSWORD' READWRITE;"
echo "Revoke user permissions"
# PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "SHOW USERS:"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "REVOKE ADMIN TO USER $USER;"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DEFAULT_DB -c "REVOKE SELECT, INSERT, CREATE, UPDATE, DELETE, DROP, ALTER ON DATABASE $DEFAULT_DB TO USER $USER;"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "REVOKE CREATE, UPDATE, DELETE, DROP, ALTER ON DATABASE $DB_NAME TO USER $USER;"
echo "Grant SELECT, INSERT"
PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "GRANT SELECT, INSERT TO USER $USER;"

echo "Check perrmissions"
# PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "SHOW GRANTS FOR $USER;"
# PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DEFAULT_DB -c "SHOW GRANTS FOR $USER;"

# PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "SHOW GRANTS;"
# PGPASSWORD="$USER_PASSWORD" psql -h $HOST -p $PORT -U $USER -d $DB_NAME -c "SHOW GRANTS;"

DB_EXEC="$(PGPASSWORD="$USER_PASSWORD" psql -h $HOST -p $PORT -U $USER -d $DEFAULT_DB -c "SHOW GRANTS FOR $USER;" 2>&1)"
DB_EXEC_CODE=$?
if [ $DB_EXEC_CODE -eq 0 ]; then
    echo "ERROR: User $USER still has access to DB $DEFAULT_DB"
    exit 1
fi

# DB_EXEC="$(PGPASSWORD="$ADMIN_PASSWORD" psql -h $HOST -p $PORT -U immudb -d $DB_NAME -c "SHOW GRANTS FOR $USER;" 2>&1)"
# echo $DB_EXEC






