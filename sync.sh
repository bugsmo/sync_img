#!/bin/bash


hub="registry.cn-guangzhou.aliyuncs.com"
repo="$hub/bitnano"


if [ -f sync.yaml ]; then
   echo "[Start] sync......."

   sudo skopeo login -u ${HUB_USERNAME} -p ${HUB_PASSWORD} ${hub} \
   && sudo skopeo --insecure-policy sync --src yaml --dest docker sync.yaml $repo \
   && sudo skopeo --insecure-policy sync --src yaml --dest docker custom_sync.yaml $repo

   echo "[End] done."
else
    echo "[Error]not found sync.yaml!"
fi

repo="$hub/kalandra"

if [ -f sync2.yaml ]; then
   echo "[Start] sync2......."

   sudo skopeo login -u ${HUB_USERNAME} -p ${HUB_PASSWORD} ${hub} \
   && sudo skopeo --insecure-policy sync --src yaml --dest docker sync2.yaml $repo

   echo "[End] done."
else
    echo "[Error]not found sync2.yaml!"
fi