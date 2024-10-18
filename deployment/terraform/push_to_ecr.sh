#!/bin/bash
ECR_URL= ## change with the output from terraform apply for ECR url
TEST_CASE_REPO="$ECR_URL/test-case-controller"
CHROME_NODE_REPO="$ECR_URL/chrome-node"

aws ecr get-login-password --region eu-north-1| docker login --username AWS --password-stdin $ECR_URL

docker tag  controller:production $TEST_CASE_REPO:production
docker push $TEST_CASE_REPO:production

docker tag  worker:production $CHROME_NODE_REPO:production
docker push $CHROME_NODE_REPO:production