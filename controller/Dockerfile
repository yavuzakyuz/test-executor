# first stage - generate protoc boilerplates
FROM golang:1.23-alpine AS build-proto

RUN apk add --no-cache git bash protobuf
    
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.28.1
RUN go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.2.0

ENV PATH="$PATH:/go/bin"

WORKDIR /app
COPY ./testexecutor-grpc/ /app/testexecutor-grpc/
WORKDIR /app/testexecutor-grpc
RUN protoc --go_out=../ --go-grpc_out=../ --go_opt=paths=source_relative --go-grpc_opt=paths=source_relative TestExecutor.proto

    
# 2nd stage - build & run the binary
FROM golang:1.23-alpine

RUN apk add --no-cache bash
    
WORKDIR /app 
COPY go.mod go.sum ./
RUN go mod download

COPY ./controller/ /app/controller/
# copy protos
COPY --from=build-proto /app/testexecutor-grpc /app/testexecutor-grpc
    
# build binary
RUN go build -o /app/controller-bin ./controller/controller.go
RUN chmod +x /app/controller-bin
    
EXPOSE 50051
    
CMD ["/app/controller-bin"]
    