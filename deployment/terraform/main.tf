
locals {
  localip = [""] # to allow ssh to ec2 on 22 inbound
}

#############################
########### ECR #############
#############################

resource "aws_ecr_repository" "controller_repo" {
  name                 = "test-case-controller"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "chrome_repo" {
  name                 = "chrome-node"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

output "test_case_controller_repo_url" {
  value = aws_ecr_repository.controller_repo.repository_url
}

output "chrome_node_repo_url" {
  value = aws_ecr_repository.chrome_repo.repository_url
}

#############################
########### VPC #############
#############################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "eks-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["eu-north-1a", "eu-north-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}

#############################
########### EKS #############
#############################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0" # The latest version of the EKS module

  cluster_name    = "insider-test-executer-cluster"
  cluster_version = "1.31"

  cluster_endpoint_public_access = true

  cluster_addons = {
    coredns                = {}
    eks-pod-identity-agent = {}
    kube-proxy             = {}
    vpc-cni                = {}
  }

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.public_subnets

  eks_managed_node_group_defaults = {
    instance_types = ["t3.large"]
  }

  eks_managed_node_groups = {
    node_group = {
      desired_size = 1
      min_size     = 1
      max_size     = 1
      ami_type     = "AL2023_x86_64_STANDARD"
    }
  }

  enable_cluster_creator_admin_permissions = true

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}

#############################
########### EC2 #############
#############################

module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 5.0"

  name = "eks-access-instance"

  instance_type               = "t3.micro"
  key_name                    = "ec2-key" # I created mine manually in portal via EC2 -> Security -> Key Pairs  
  monitoring                  = true
  vpc_security_group_ids      = [module.vpc.default_security_group_id]
  subnet_id                   = module.vpc.public_subnets[0]
  associate_public_ip_address = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

# allow ssh access
resource "aws_security_group_rule" "allow_ssh" {
  security_group_id = module.vpc.default_security_group_id
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = local.localip
}

# allow internet access / for installing kubectl
resource "aws_security_group_rule" "allow_internet_access" {
  security_group_id = module.vpc.default_security_group_id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}
