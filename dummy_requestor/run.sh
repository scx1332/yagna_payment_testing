#! /bin/bash
set -x
export PATH=".:$PATH"

poetry run python main.py \
  --check-for-yagna false \
  --subnet-tag ${SUBNET:-bor_proxy_subnet} \
  --num-instances ${SERVICE_NUM_INSTANCES:-2} \
  --service ${SERVICE_NAME:-bor-service} \
  --node-running-time 30,31


