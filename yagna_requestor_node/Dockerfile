# change token to bypass docker caching system
ARG YAGNA_GIT_CLONE_CACHE_TOKEN=6a8e3564-a91f-4c3e-8f4f-3ab5ff0f6608
# can be used to specify a branch or tag
ARG YAGNA_BRANCH_TAG_OR_COMMIT=master
# dev, release
ARG YAGNA_BUILD_PROFILE=dev
# x86_64-unknown-linux-musl or x86_64-unknown-linux-gnu
ARG YAGNA_BUILD_TARGET=x86_64-unknown-linux-musl
# yagna additional features
ARG YAGNA_FEATURES=static-openssl

FROM rust as build
#repeat ARGs to make them available in the next stage
RUN apt-get update
RUN apt-get install cmake openssl musl-tools -y
ARG YAGNA_GIT_CLONE_CACHE_TOKEN
ARG YAGNA_BRANCH_TAG_OR_COMMIT
RUN echo ${YAGNA_GIT_CLONE_CACHE_TOKEN} && git clone https://github.com/golemfactory/yagna.git yagna && cd yagna && git checkout ${YAGNA_BRANCH_TAG_OR_COMMIT}
# remove local version overrides and compile with provided version
RUN cd yagna && rm rust-toolchain.toml
ARG YAGNA_BUILD_PROFILE
ARG YAGNA_BUILD_TARGET
ARG YAGNA_FEATURES
ENV CARGO_BUILD_TARGET=${YAGNA_BUILD_TARGET}
RUN cd yagna && cargo build --target-dir build --profile ${YAGNA_BUILD_PROFILE} --target ${YAGNA_BUILD_TARGET} --features ${YAGNA_FEATURES}


FROM python:3.9
ENV PATH=".:${PATH}"

WORKDIR /yagna

# download release yagna binaries
COPY --from=0 /yagna/target/${YAGNA_BUILD_TARGET}/${YAGNA_BUILD_MODE}/yagna .
COPY --from=0 /yagna/target/${YAGNA_BUILD_TARGET}/${YAGNA_BUILD_MODE}/gftp .

# install python requirements for yagna_mon.py
RUN pip install quart requests

# run script + monitor
COPY run.sh .
RUN chmod +x run.sh

COPY yagna_mon.py .

