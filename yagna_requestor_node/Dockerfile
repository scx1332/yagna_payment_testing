# change token to bypass docker caching system
# after changing you get clean build from scratch
ARG YAGNA_GIT_CLONE_CACHE_TOKEN=6a8e3564-a91f-4c3e-8f4f-3ab5ff0f6608
# change token to build incremental changes pulling changes from the branch and doing a cargo build
ARG YAGNA_INCREMENTAL_BUILD_TOKEN=ae3f37c9-d95a-4375-9d87-43fbe0dd12dc
# can be used to specify a branch or tag
ARG YAGNA_BRANCH_OR_TAG=master
# dev, release (use dev when build speed is more important than yagna speed)
ARG YAGNA_BUILD_PROFILE=release
# x86_64-unknown-linux-musl or x86_64-unknown-linux-gnu
ARG YAGNA_BUILD_TARGET=x86_64-unknown-linux-musl
# yagna additional features
ARG YAGNA_FEATURES=static-openssl

FROM rust as yagna-build
#repeat ARGs to make them available in the next stage
RUN apt-get update
RUN apt-get install cmake openssl musl-tools -y
ARG YAGNA_GIT_CLONE_CACHE_TOKEN
RUN echo ${YAGNA_GIT_CLONE_CACHE_TOKEN} && git clone https://github.com/golemfactory/yagna.git yagna
WORKDIR /yagna
ARG YAGNA_BRANCH_OR_TAG
RUN git pull && git checkout ${YAGNA_BRANCH_OR_TAG}
# remove local version overrides and compile with provided version
RUN rm rust-toolchain.toml
# this step is to separate downloading dependencies from building greatly improving speed of rebuilds if build breaks
RUN cargo fetch
# override cargo config with provided one
COPY yagna_cargo_config.toml .cargo/config
# build yagna
ARG YAGNA_BUILD_PROFILE
ARG YAGNA_BUILD_TARGET
ARG YAGNA_FEATURES
RUN rustup target add ${YAGNA_BUILD_TARGET}
RUN cargo build --all --profile ${YAGNA_BUILD_PROFILE} --target ${YAGNA_BUILD_TARGET} --features ${YAGNA_FEATURES}
# update for incremental builds
ARG YAGNA_INCREMENTAL_BUILD_TOKEN
RUN echo ${YAGNA_INCREMENTAL_BUILD_TOKEN} && git pull
RUN cargo build --all --profile ${YAGNA_BUILD_PROFILE} --target ${YAGNA_BUILD_TARGET} --features ${YAGNA_FEATURES}
# map /build diretory to directory containing yagna binaries
# we have to use this ugly "if" because profile dev is mapped to debug
RUN if [ "${YAGNA_BUILD_PROFILE}" = "dev" ] ; then ln -s /yagna/target/${YAGNA_BUILD_TARGET}/debug /build ; else ln -s /yagna/target/${YAGNA_BUILD_TARGET}/${YAGNA_BUILD_PROFILE} /build ; fi


FROM rust as ya-runtime-http-build
RUN apt-get update
RUN apt-get install cmake openssl musl-tools -y
RUN git clone --single-branch --branch main https://github.com/golemfactory/ya-runtime-http-auth.git ya-runtime-http-auth
WORKDIR /ya-runtime-http-auth
RUN cargo build --release
RUN cargo build --release -p ya-http-proxy --bin ya-http-proxy --features="bin"
# generate self signed certificate for use in proxy
RUN mkdir /privatecerts
WORKDIR /privatecerts
RUN openssl req -nodes -x509 -newkey rsa:4096 -keyout server.key -out server.cert -sha256 -days 3650 -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=www.example.com"


FROM python:3.11
RUN apt-get update
# install common helpful tools
RUN apt-get install -y curl vim jq net-tools htop
# install python requirements for yagna_mon.py
RUN pip install quart requests

WORKDIR /yagna

# download release yagna binaries
COPY --from=yagna-build /build/yagna /usr/bin
COPY --from=yagna-build /build/gftp /usr/bin
COPY --from=yagna-build /build/ya-provider /usr/bin
COPY --from=yagna-build /build/golemsp /usr/bin
COPY --from=yagna-build /build/exe-unit /root/.local/lib/yagna/plugins/exe-unit
RUN mkdir /root/.local/lib/yagna/plugins/ya-runtime-bor
RUN mkdir /privatecerts
COPY plugins /root/.local/lib/yagna/plugins
COPY ya-provider /root/.local/share/ya-provider
COPY --from=ya-runtime-http-build /ya-runtime-http-auth/target/release/ya-http-proxy /root/.local/lib/yagna/plugins/ya-runtime-bor
COPY --from=ya-runtime-http-build /ya-runtime-http-auth/target/release/ya-runtime-http-auth /root/.local/lib/yagna/plugins/ya-runtime-bor
COPY --from=ya-runtime-http-build /privatecerts/server.cert /privatecerts/server.cert
COPY --from=ya-runtime-http-build /privatecerts/server.key /privatecerts/server.key

COPY *.sh .
RUN chmod +x *.sh

COPY yagna_mon.py .

