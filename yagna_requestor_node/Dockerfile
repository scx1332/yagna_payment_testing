FROM rust as build
RUN apt-get update
RUN apt-get install cmake openssl musl-tools -y
RUN git clone --single-branch --branch master https://github.com/golemfactory/yagna.git yagna
RUN cd yagna && cargo build --release --all --target x86_64-unknown-linux-musl --features static-openssl

FROM python:3.9

ENV PATH=".:${PATH}"

WORKDIR /yagna

# download release yagna binaries
COPY --from=0 /yagna/target/x86_64-unknown-linux-musl/release/yagna .
COPY --from=0 /yagna/target/x86_64-unknown-linux-musl/release/gftp .

# install python requirements for yagna_mon.py
RUN pip install quart requests

# run script + monitor
COPY run.sh .
RUN chmod +x run.sh

COPY yagna_mon.py .

