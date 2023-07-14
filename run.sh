#!/bin/bash

set -e
(
if lsof -Pi :27017 -sTCP:LISTEN -t >/dev/null ; then
    echo "Please terminate the local mongod on 27017"
    exit 1
fi
)
arch=$(uname -m)

# Apple M1 laptops running MongoDB 5.x inside Docker is currently not supported so we check and install latest 4.4 build 
if [[ "${arch}" == "arm64" ]]; then
    export PLATFORM=linux/amd64 && export MDBVERSION="mongo:4.4.14" && export MDBSHELL="/usr/bin/mongo"
else
    export PLATFORM=linux/x86_64 && export MDBVERSION="mongo:latest" && export MDBSHELL="/usr/bin/mongosh"
fi
echo "\nRunning on ${arch} setting platform to ${PLATFORM} and pulling MongoDB Version ${MDBVERSION}"

echo "Starting docker ."
docker-compose up -d --build

sleep 5

echo "\nConfiguring the MongoDB ReplicaSet...\n"
# 5.0 and above we can use mongosh else we use the oild mongo shell
# host : "localhost:27017". Use localhost for the replica set configuration that are accessible by the host so that pymongo have access
docker-compose exec mongo1 ${MDBSHELL} --eval '''rsconf = { _id : "rs0", members: [ { _id : 0, host : "localhost:27017", priority: 1.0 }]}; rs.initiate(rsconf);'''

echo '''
==============================================================================================================
The following services are running:

MongoDB on 27017
==============================================================================================================
'''