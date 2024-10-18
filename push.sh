#!/bin/bash
CONTROLLER_IMAGE="k3d-k3d-registry.local:5100/controller:beta-v14"
WORKER_IMAGE="k3d-k3d-registry.local:5100/worker:beta-v14"

docker build -t $CONTROLLER_IMAGE -f ./controller/Dockerfile .
if [ $? -ne 0 ]; then
  echo "failed to build controller"
  exit 1
fi

docker push $CONTROLLER_IMAGE
if [ $? -ne 0 ]; then
  echo "failed to push"
  exit 1
fi

docker build -t $WORKER_IMAGE -f ./worker/Dockerfile .
if [ $? -ne 0 ]; then
  echo "failed to build worker"
  exit 1
fi

docker push $WORKER_IMAGE
if [ $? -ne 0 ]; then
  echo "failed to push"
  exit 1
fi
