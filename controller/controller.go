package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"path/filepath"
	"strings"
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
	mu         sync.Mutex            // mutex for the race condition (not sure if it'll happen for our case)
	workers    map[string]WorkerInfo // worker uuid map for lookups
	workerList []string              // slice because map didn't keep the worker join order
	nextWorker int                   // keeps track of the next worker to receive a task (basic RR scheduling, can be improved)
	testCases  []string              // test cases under controler/tests
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
	s.workerList = append(s.workerList, workerID) // add worker to list
	fmt.Printf("a new worker joined to the queue! - worker-%s\n", workerID)

	return &pb.HandshakeResponse{Response: "handshake acknowledged"}, nil
}

func loadTestCases(testDir string) ([]string, error) {
	files, err := os.ReadDir(testDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read tests directory: %v", err)
	}

	var testCases []string
	for _, file := range files {
		if !file.IsDir() && strings.HasSuffix(file.Name(), ".py") {
			testCases = append(testCases, filepath.Join(testDir, file.Name()))
		}
	}
	return testCases, nil
}

// send and wait for a worker to receive a task (test py file)
func (s *server) ReceiveTask(ctx context.Context, req *pb.Empty) (*pb.TaskResponse, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// check if any workers are available
	if len(s.workers) == 0 {
		return nil, fmt.Errorf("no workers available")
	}

	// check if there are test cases available
	if len(s.testCases) == 0 {
		return nil, fmt.Errorf("no test cases available")
	}

	// select the next worker for the next task
	workerID := s.workerList[s.nextWorker%len(s.workerList)] // Round-robin selection even with one worker
	worker := s.workers[workerID]

	// choose the test case to send (wrap around the test cases if one worker)
	testFile := s.testCases[s.nextWorker%len(s.testCases)]
	fileContent, err := os.ReadFile(testFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read test file: %v", err)
	}

	fmt.Printf("sending task '%s' to worker-%s\n", testFile, worker.ID)

	// update the nextWorker counter to distribute the next task
	s.nextWorker = (s.nextWorker + 1) % len(s.testCases) // wrap around the test cases

	// send the test file to the worker
	return &pb.TaskResponse{
		Filename: filepath.Base(testFile),
		Content:  fileContent,
		Message:  "run the test script",
	}, nil
}

func main() {
	// load all test cases from the tests folder
	testCases, err := loadTestCases("controller/tests")
	if err != nil {
		log.Fatalf("failed to load test cases: %v", err)
	}

	// print loaded cases
	fmt.Printf("loaded %d test cases:\n", len(testCases))
	for _, testCase := range testCases {
		fmt.Printf(" - %s\n", filepath.Base(testCase))
	}

	// grpc server on 50051
	fmt.Printf("Started accepting worker nodes\n")

	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("can't listen on port 50051: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterTestExecutorServer(s, &server{
		workers:    make(map[string]WorkerInfo),
		workerList: []string{},
		nextWorker: 0,
		testCases:  testCases, // pass the loaded test cases to the server
	})

	fmt.Println("controller waiting for workers on port 50051...")

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
