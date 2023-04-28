#!/bin/sh

port=$1

# step 1. config

f=mirrormanager2/client_secrets.json

sed -i "s|{OIDC_CLIENT_ID}|$OIDC_CLIENT_ID|"  $f
sed -i "s|{OIDC_CLIENT_SECRET}|$OIDC_CLIENT_SECRET|"  $f
sed -i "s|{OIDC_AUTH_URI}|$OIDC_AUTH_URI|"  $f
sed -i "s|{OIDC_TOKEN_URI}|$OIDC_TOKEN_URI|"  $f
sed -i "s|{MM_ENDPOINT}|$MM_ENDPOINT|"  $f
sed -i "s|{OIDC_USERINFO_URI}|$OIDC_USERINFO_URI|"  $f
sed -i "s|{OIDC_ISSUER}|$OIDC_ISSUER|"  $f

###

f=mirrormanager2/default_config.py

sed -i "s|{DB_URL}|$DB_URL|"  $f
sed -i "s|{SECRET_KEY}|$SECRET_KEY|"  $f
sed -i "s|{PASSWORD_SEED}|$PASSWORD_SEED|"  $f

ADMIN_GROUP="\'$ADMIN_GROUP\'"
ADMIN_GROUP=$(echo $ADMIN_GROUP | sed -e "s|,|','|g")

sed -i "s|{ADMIN_GROUP}|$ADMIN_GROUP|"  $f

###

f=utility/config/mirrormanager2.cfg

sed -i "s|{DB_URL}|$DB_URL|"  $f
sed -i "s|{SECRET_KEY}|$SECRET_KEY|"  $f
sed -i "s|{PASSWORD_SEED}|$PASSWORD_SEED|"  $f
sed -i "s|{UMDL_PREFIX}|$UMDL_PREFIX|"  $f

# step 2. create db

python3 createdb.py

# step 3. run server

python3 runserver.py --host 0.0.0.0 --port $port

