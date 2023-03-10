#! /bin/bash
set -x
export PATH=".:$PATH"

poetry run python main.py \
  --check-for-yagna false \
  --subnet-tag ${SUBNET:-bor_proxy_subnet} \
  --num-instances ${SERVICE_NUM_INSTANCES:-2} \
  --service ${SERVICE_NAME:-bor-service} \
  --node-running-time ${SERVICE_NODE_RUNNING_TIME:-30,31} \
  --network ${PAYMENT_NETWORK:-rinkeby} \
  --driver ${PAYMENT_DRIVER:-erc20}


