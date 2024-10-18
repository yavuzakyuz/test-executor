#!/bin/bash
ECR_URL= ### change with the output from terraform apply for ECR url
TEST_CASE_REPO="$ECR_URL/test-case-controller"
CHROME_NODE_REPO="$ECR_URL/chrome-node"

aws ecr get-login-password --region eu-north-1| docker login --username AWS --password-stdin $ECR_URL

docker build --platform linux/amd64 \
  -t $TEST_CASE_REPO:production \
  -f ./controller/Dockerfile .
docker push $TEST_CASE_REPO:production

docker build --platform linux/amd64 \
  -t $CHROME_NODE_REPO:production \
  -f ./worker/Dockerfile .
docker push $CHROME_NODE_REPO:production
