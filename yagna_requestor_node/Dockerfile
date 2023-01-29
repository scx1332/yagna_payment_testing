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
# build yagna
ARG YAGNA_BUILD_PROFILE
ARG YAGNA_BUILD_TARGET
ARG YAGNA_FEATURES
RUN rustup target add ${YAGNA_BUILD_TARGET}
RUN cargo build --profile ${YAGNA_BUILD_PROFILE} --target ${YAGNA_BUILD_TARGET} --features ${YAGNA_FEATURES}
# update for incremental builds
ARG YAGNA_INCREMENTAL_BUILD_TOKEN
RUN echo ${YAGNA_INCREMENTAL_BUILD_TOKEN} && git pull
RUN cargo build --profile ${YAGNA_BUILD_PROFILE} --target ${YAGNA_BUILD_TARGET} --features ${YAGNA_FEATURES}
# we have to write this ugly if because profile dev is mapped to debug

RUN if [ "${YAGNA_BUILD_PROFILE}" = "dev" ] ; then ln -s /yagna/target/${YAGNA_BUILD_TARGET}/debug /build ; else ln -s /yagna/target/${YAGNA_BUILD_TARGET}/${YAGNA_BUILD_PROFILE} /build ; fi


FROM python:3.9
ENV PATH=".:${PATH}"

WORKDIR /yagna

# download release yagna binaries
COPY --from=yagna-build /build/yagna .
COPY --from=yagna-build /build/gftp .

# install python requirements for yagna_mon.py
RUN pip install quart requests

# run script + monitor
COPY run.sh .
RUN chmod +x run.sh

COPY yagna_mon.py .

