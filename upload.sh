#!/usr/bin/env bash

DATA=$( cat ./metrics )
echo "data: { $DATA }"

curl \
    -X POST \
    -d "{ \"user\": { \"public_key\": \"6546b543a35b7d5af8c93a7b\", \"private_key\": $PRIVATE_KEY }, \"sha\": \"$TO\", \"metrics\": { $DATA } }" \
    -H "Content-Type: application/json" \
    -i http://3.10.39.149:3000/metrics