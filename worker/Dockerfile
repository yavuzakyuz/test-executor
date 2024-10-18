FROM selenium/standalone-chrome:119.0-20231110
# FROM selenium/node-chrome:129.0-20241010
USER root
RUN apt-get update && apt-get install -y \
    software-properties-common \
    golang python3-pip python3-venv bash \
    protobuf-compiler

   
RUN add-apt-repository ppa:longsleep/golang-backports
RUN apt-get update && apt-get install -y golang-go
   
ENV PATH="/usr/local/go/bin:${PATH}"
    
ENV GO111MODULE=on

RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.28.1
RUN go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.2.0
    
ENV PATH="$PATH:/go/bin"

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
    
   
COPY worker/insider_py_wrapper/requirements.txt ./insider_py_wrapper/
COPY worker/insider_py_wrapper/ ./insider_py_wrapper/
    

RUN pip3 install virtualenv
    
# create virtual env for downloading modules
RUN python3 -m venv /app/insider_py_wrapper/env
RUN /app/insider_py_wrapper/env/bin/pip3 install -r /app/insider_py_wrapper/requirements.txt
    
COPY worker/ /app/worker/
COPY testexecutor-grpc/ /app/testexecutor-grpc/
    
RUN export PATH=$PATH:/go/bin && echo $PATH
    

WORKDIR /app/testexecutor-grpc
##RUN protoc --plugin=~/go/bin/protoc-gen-go --go_out=../ --plugin=/go/bin/protoc-gen-go-grpc --go-grpc_out=../ TestExecutor.proto
    
WORKDIR /app
   
RUN go mod download
RUN go build -o /app/worker-bin ./worker/worker.go
RUN chmod +x /app/worker-bin
    
EXPOSE 50052
CMD ["bash", "-c", "source /app/insider_py_wrapper/env/bin/activate && ./worker-bin"]