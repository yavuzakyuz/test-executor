package main

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"time"

	pb "insider-test-executor/testexecutor-grpc"

	"github.com/google/uuid"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func createUniqueID() string {
	id := uuid.New()
	return id.String()[:6]
}

func main() {

	worker_id := createUniqueID() // first all workers need to create an UUID

	// added later: get env value for controller svc url
	controllerAddress := os.Getenv("CONTROLLER_URL")
	if controllerAddress == "" {
		controllerAddress = "localhost:50051" // defaults to localh
	}

	// connect to gRPC server as a client on 50051
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	conn, err := grpc.NewClient(controllerAddress, opts...)
	if err != nil {
		log.Fatalf("failed to connect to controller: %v", err)
	}
	defer conn.Close()

	client := pb.NewTestExecutorClient(conn)

	// timeout for context, no problems so far
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
	defer cancel()

	req := &pb.HandshakeRequest{Message: worker_id}
	// here the worker inits the handshake, so they can just do the test and exit. no state or for loop unless
	// there's a controller
	resp, err := client.StartHandshake(ctx, req)
	if err != nil {
		log.Fatalf("failed to start handshake: %v", err)
	}
	fmt.Printf("handshake successful: %s\n", resp.GetResponse())

	// when handshake is done, start waiting for the test task from controller
	for {
		fileCtx, fileCancel := context.WithTimeout(context.Background(), time.Minute*5) // can make this less but 1 was not enough
		defer fileCancel()

		// server sends the test py via ReceiveTask
		taskResp, err := client.ReceiveTask(fileCtx, &pb.Empty{})
		if err != nil {
			log.Printf("failed to receive task: %v", err)
			break // let controller know it failed to receive the file
		}

		// take the file, write it into the same dir
		err = os.WriteFile(taskResp.Filename, taskResp.Content, 0644)
		if err != nil {
			log.Fatalf("failed to write task file: %v", err)
		}
		fmt.Printf("received and saved task file: %s\n", taskResp.Filename)

		// env will come preloaded from the dockerfile, so we don't need to install anything (maybe tests are on local network and pods will be blocked from internet access)
		// just activate the python env for dependencies
		cmd := exec.Command("./insider_py_wrapper/env/bin/python3", taskResp.Filename)
		cmd.Env = os.Environ() // i'm not %100 sure if this is required

		// pipes for real time logging, otherwise it's buffering
		stdoutPipe, _ := cmd.StdoutPipe()
		stderrPipe, _ := cmd.StderrPipe()

		if err := cmd.Start(); err != nil {
			log.Fatalf("failed to start test script: %v", err)
		}

		// goroutines for writing all the logs live
		go readPipeOutput(stdoutPipe, "stdout")
		go readPipeOutput(stderrPipe, "stderr")

		// wait for the command to complete
		if err := cmd.Wait(); err != nil {
			log.Fatalf("python test script execution failed: %v", err)
		}

		break // job done/shut the container down,
		// we can keep it alive too, but deciding this via kube seems better
	}
}

// helper function to read and log the logs from python runtime, calling it with goroutines
func readPipeOutput(pipe io.ReadCloser, pipeName string) {
	scanner := bufio.NewScanner(pipe)
	for scanner.Scan() {
		log.Printf("[%s] %s\n", pipeName, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		log.Printf("error reading from %s: %v", pipeName, err)
	}
}
