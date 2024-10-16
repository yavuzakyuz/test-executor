package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"sync"

	pb "insider-test-executor/testexecutor-grpc"

	"google.golang.org/grpc"
)

// worker struct for distributing/scheduling the tests
type WorkerInfo struct {
	ID      string
	Address string
}

// gRPC server struct
type server struct {
	pb.UnimplementedTestExecutorServer
	mu         sync.Mutex            // mutex for race condition
	workers    map[string]WorkerInfo // worker uuid map for lookups
	workerList []string              // slice because map didn't keep the worker join order
	nextWorker int                   // keeps track of the next worker to receive a task (basic RR scheduling, can be improved)
}

// wait handshake
func (s *server) StartHandshake(ctx context.Context, req *pb.HandshakeRequest) (*pb.HandshakeResponse, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	workerID := req.GetMessage()
	workerInfo := WorkerInfo{
		ID: workerID,
	}
	s.workers[workerID] = workerInfo
	s.workerList = append(s.workerList, workerID) // Add worker to list
	fmt.Printf("a new worker joined to the queue! - worker-%s\n", workerID)

	return &pb.HandshakeResponse{Response: "handshake acknowledged"}, nil
}

// send and wait for a worker to receive a task (test py file)
func (s *server) ReceiveTask(ctx context.Context, req *pb.Empty) (*pb.TaskResponse, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// check if any workers are available
	if len(s.workers) == 0 {
		return nil, fmt.Errorf("no workers available, are you sure any are alive?")
	}

	// select the next worker for the next task
	workerID := s.workerList[s.nextWorker]
	worker := s.workers[workerID]

	// update the nextWorker counter to the next one in line for the next task
	s.nextWorker = (s.nextWorker + 1) % len(s.workers)

	fmt.Printf("sending task to worker %s\n", worker.ID)

	// read the test py script (same dir)
	pyFile := "main.py"
	fileContent, err := os.ReadFile(pyFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read python file. Is the file in the same dir?: %v", err)
	}

	// send the test file to the worker & command run
	return &pb.TaskResponse{
		Filename: pyFile,
		Content:  fileContent,
		Message:  "run the test script",
	}, nil
}

func main() {
	// grpc server on 50051
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("can't listen on port 50051: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterTestExecutorServer(s, &server{
		workers:    make(map[string]WorkerInfo),
		workerList: []string{}, // worker list init
		nextWorker: 0,          // worker counter init
	})

	fmt.Println("controller waiting for workers on port 50051...")

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
