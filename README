# System Architecture 

# Folder structure 

We have 4 directories for the project:  

insider-testops-yavuz/
│
├── controller/       
│   ├── main.go      
│   └── go.mod        
│
├── worker/          
│   ├── main.go       
│   └── go.mod        
│
├── testexecutor-grpc/            
│   ├── test.proto   
│
│
├── deployment/            
    ├── terraform
    ├── cluster


# Complete installation steps

### Install golang/protobuf for running proto for go (https://grpc.io/docs/languages/go/quickstart/#prerequisites)

homebrew (for my local system): 
$ brew install protobuf
linux: 
$ sudo apt install -y protobuf-compiler
 
### Export path -if not done before- so protoc can use go plugins

$ export PATH="$PATH:$(go env GOPATH)/bin"

### Install go protoc plugins for generating boilerplates 
$ go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
$ go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest


### Generate go code 
cd to the protoc: 
$ cd testexecutor-grpc
generate pb.go files
$ protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    TestExecutor.proto


### Build Docker images

Needed multistage docker build as proto files couldnt't be copied... 
(https://stackoverflow.com/questions/48791388/sharing-proto-files-in-docker)

also selenium/standalone-chrome base image 
had 1.21 as the latest golang available in apt-get repo
which didn't include slices and wasn't compatible with 
latest stable grpc plugins in golang, installed via ppa: https://go.dev/wiki/Ubuntu

#### Controller 
$ docker build -t controller:beta -f ./controller/Dockerfile .
$ docker run -d --name controller -p 50051:50051 test-controller

#### Worker
macos (arm64): 
docker build -t worker:beta -f ./worker/Dockerfile . --platform linux/amd64
docker run -d -p 50052:50052 --platform linux/amd64 worker:beta 
linux:
docker build -t worker:beta -f ./worker/Dockerfile .
docker run -d worker:beta -p 50052:50052

