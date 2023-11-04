#!/usr/bin/env bash

curl \
    -X GET \
    -d "{ \"user\": { \"public_key\": \"6546b543a35b7d5af8c93a7b\", \"private_key\": $PRIVATE_KEY }, \"from\": \"$FROM\", \"to\": \"$TO\" }" \
    -H "Content-Type: application/json" \
    -i http://3.10.39.149:3000/diff_pretty