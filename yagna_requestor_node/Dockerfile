FROM rust as build
RUN apt-get update
RUN apt-get install cmake openssl musl-tools -y
RUN git clone --single-branch --branch master https://github.com/golemfactory/yagna.git yagna
RUN cd yagna && cargo build --release --all --target x86_64-unknown-linux-musl --features static-openssl

FROM python:3.9

ENV PATH=".:${PATH}"

WORKDIR /yagna

# download release yagna binaries
ADD https://github.com/golemfactory/yagna/releases/download/v0.10.1/golem-requestor-linux-v0.10.1.tar.gz .
RUN tar -xvf golem-requestor-linux-v0.10.1.tar.gz
RUN mv golem-requestor-linux-v0.10.1/gftp .
COPY --from=0 /yagna/target/x86_64-unknown-linux-musl/release/yagna .
RUN rm -fr golem-requestor-linux-v0.10.1
RUN rm golem-requestor-linux-v0.10.1.tar.gz
RUN chmod +x gftp
RUN chmod +x yagna

# install python requirements for yagna_mon.py
RUN pip install quart requests

# run script + monitor
COPY run.sh .
RUN chmod +x run.sh

COPY yagna_mon.py .

