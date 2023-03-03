#! /bin/bash

export YAGNA_AUTOCONF_APPKEY=${YAGNA_AUTOCONF_APPKEY-q$RANDOM$RANDOM}
export YAGNA_APPKEY=${YAGNA_AUTOCONF_APPKEY}
export PAYMENT_NETWORK=${PAYMENT_NETWORK:-rinkeby}
export PAYMENT_DRIVER=${PAYMENT_DRIVER:-erc20}
export SUBNET=${SUBNET:-payment_testing_subnet}
export NODE_NAME=${NODE_NAME:-polygon_proxy}
export YA_PAYMENT_NETWORK=${PAYMENT_NETWORK}
export YA_PAYMENT_DRIVER=${PAYMENT_DRIVER}

export HTTPS_PORT=${HTTPS_PORT:-1443}
export HTTP_PORT=${HTTP_PORT:-1180}
export SERVER_NAME=${SERVER_NAME:-bor-proxy-provider}
export TARGET_PROXY=${TARGET_PROXY:-http://golem.network}
export SERVICE_NAME=${SERVICE_NAME:-bor-service}
export SERVICE_DESCRIPTION=${SERVICE_DESCRIPTION:-BorService}

export MAX_AGREEMENTS=${MAX_AGREEMENTS:-1}
export MIN_AGREEMENT_EXPIRATION=${MIN_AGREEMENT_EXPIRATION:-5s}

YA_RUNTIME_BOR_DIR=/root/.local/lib/yagna/plugins/ya-runtime-bor
sed -i 's/%%HTTPS_PORT%%/'$HTTPS_PORT'/g' $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt
sed -i 's/%%HTTP_PORT%%/'$HTTP_PORT'/g' $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt
sed -i 's/%%SERVER_NAME%%/'$SERVER_NAME'/g' $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt
sed -i 's#%%TARGET_PROXY%%#'$TARGET_PROXY'#g' $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt
sed -i 's#%%SERVICE_NAME%%#'$SERVICE_NAME'#g' $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt
sed -i 's#%%SERVICE_DESCRIPTION%%#'$SERVICE_DESCRIPTION'#g' $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt
cp $YA_RUNTIME_BOR_DIR/services/bor-service-template.txt $YA_RUNTIME_BOR_DIR/services/bor-service.json

yagna service run &
sleep 5
yagna id list
yagna payment init --receiver --driver erc20 --network $PAYMENT_NETWORK
ya-provider run --max-simultaneous-agreements $MAX_AGREEMENTS --min-agreement-expiration $MIN_AGREEMENT_EXPIRATION

echo "Waiting for 30 seconds before leaving the container..."
sleep 30
echo "Leaving the container..."

