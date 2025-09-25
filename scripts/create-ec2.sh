#!/bin/bash
# Create EC2 instance for BodyScript deployment
# This script creates a t2.micro instance optimized for the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Modify these as needed
INSTANCE_NAME="${INSTANCE_NAME:-bodyscript-server}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t2.micro}"
KEY_NAME="${KEY_NAME:-bodyscript-key}"
REGION="${REGION:-us-east-1}"
AMI_ID="${AMI_ID:-}"  # Will auto-detect Ubuntu 22.04 LTS if not provided
SECURITY_GROUP_NAME="${SECURITY_GROUP_NAME:-bodyscript-sg}"
VOLUME_SIZE="${VOLUME_SIZE:-20}"  # GB

echo "🚀 Creating EC2 Instance for BodyScript"
echo "═══════════════════════════════════════"
echo ""

# Check if AWS CLI is installed
if ! command -v aws >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not installed${NC}"
    echo "Install with: brew install awscli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

echo "📍 Configuration:"
echo "   Region:        $REGION"
echo "   Instance Type: $INSTANCE_TYPE"
echo "   Instance Name: $INSTANCE_NAME"
echo "   Key Pair:      $KEY_NAME"
echo ""

# Step 1: Get latest Ubuntu 22.04 LTS AMI if not provided
if [ -z "$AMI_ID" ]; then
    echo "🔍 Finding latest Ubuntu 22.04 LTS AMI..."
    AMI_ID=$(aws ec2 describe-images \
        --region $REGION \
        --owners 099720109477 \
        --filters \
            "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
            "Name=virtualization-type,Values=hvm" \
            "Name=architecture,Values=x86_64" \
            "Name=root-device-type,Values=ebs" \
            "Name=state,Values=available" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)

    if [ -z "$AMI_ID" ] || [ "$AMI_ID" = "None" ]; then
        echo -e "${RED}❌ Could not find Ubuntu 22.04 AMI${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Found AMI: $AMI_ID${NC}"
else
    echo "📦 Using provided AMI: $AMI_ID"
fi
echo ""

# Step 2: Create or verify key pair
echo "🔑 Setting up SSH key pair..."
KEY_FILE="$HOME/.ssh/$KEY_NAME.pem"

if aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Key pair '$KEY_NAME' already exists${NC}"
    if [ ! -f "$KEY_FILE" ]; then
        echo -e "${RED}❌ Key file not found at $KEY_FILE${NC}"
        echo "   If you have the key elsewhere, copy it to: $KEY_FILE"
        echo "   Or delete the key pair and re-run this script:"
        echo "   aws ec2 delete-key-pair --key-name $KEY_NAME --region $REGION"
        exit 1
    fi
else
    echo "Creating new key pair..."
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $REGION \
        --query 'KeyMaterial' \
        --output text > "$KEY_FILE"

    chmod 600 "$KEY_FILE"
    echo -e "${GREEN}✅ Key pair created: $KEY_FILE${NC}"
fi
echo ""

# Step 3: Create security group
echo "🔒 Setting up security group..."
VPC_ID=$(aws ec2 describe-vpcs \
    --region $REGION \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text)

if aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Security group '$SECURITY_GROUP_NAME' already exists${NC}"
    SG_ID=$(aws ec2 describe-security-groups \
        --group-names $SECURITY_GROUP_NAME \
        --region $REGION \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
else
    echo "Creating new security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP_NAME \
        --description "Security group for BodyScript application" \
        --vpc-id $VPC_ID \
        --region $REGION \
        --query 'GroupId' \
        --output text)

    echo "Adding security rules..."

    # SSH access
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $REGION >/dev/null 2>&1 || true

    # HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $REGION >/dev/null 2>&1 || true

    # HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region $REGION >/dev/null 2>&1 || true

    # API port (optional, for testing)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region $REGION >/dev/null 2>&1 || true

    # Nginx port (for testing)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8080 \
        --cidr 0.0.0.0/0 \
        --region $REGION >/dev/null 2>&1 || true

    echo -e "${GREEN}✅ Security group created: $SG_ID${NC}"
fi
echo ""

# Step 4: Create EC2 instance
echo "🖥️  Launching EC2 instance..."

# User data script to pre-install Docker and Nginx
USER_DATA=$(cat << 'EOF'
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose nginx certbot python3-certbot-nginx
usermod -aG docker ubuntu
systemctl start docker
systemctl enable docker
systemctl start nginx
systemctl enable nginx
mkdir -p /home/ubuntu/bodyscript/{nginx,scripts,backend/temp,frontend}
chown -R ubuntu:ubuntu /home/ubuntu/bodyscript
EOF
)

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $REGION \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_SIZE,VolumeType=gp3,DeleteOnTermination=true}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --user-data "$USER_DATA" \
    --query 'Instances[0].InstanceId' \
    --output text)

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "None" ]; then
    echo -e "${RED}❌ Failed to create instance${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Instance created: $INSTANCE_ID${NC}"
echo ""

# Step 5: Wait for instance to be running
echo "⏳ Waiting for instance to start..."
aws ec2 wait instance-running \
    --instance-ids $INSTANCE_ID \
    --region $REGION

# Get instance details
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

PUBLIC_DNS=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicDnsName' \
    --output text)

echo -e "${GREEN}✅ Instance is running!${NC}"
echo ""

# Step 6: Allocate and associate Elastic IP (optional but recommended)
read -p "Do you want to allocate an Elastic IP? (recommended for production) (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📍 Allocating Elastic IP..."

    ALLOCATION_ID=$(aws ec2 allocate-address \
        --domain vpc \
        --region $REGION \
        --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$INSTANCE_NAME-eip}]" \
        --query 'AllocationId' \
        --output text)

    aws ec2 associate-address \
        --instance-id $INSTANCE_ID \
        --allocation-id $ALLOCATION_ID \
        --region $REGION >/dev/null

    # Get the new Elastic IP
    ELASTIC_IP=$(aws ec2 describe-addresses \
        --allocation-ids $ALLOCATION_ID \
        --region $REGION \
        --query 'Addresses[0].PublicIp' \
        --output text)

    echo -e "${GREEN}✅ Elastic IP allocated: $ELASTIC_IP${NC}"
    PUBLIC_IP=$ELASTIC_IP
fi
echo ""

# Step 7: Wait for instance to be ready for SSH
echo "⏳ Waiting for SSH to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$KEY_FILE" ubuntu@$PUBLIC_IP "echo 'SSH ready'" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ SSH is ready${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${YELLOW}⚠️  SSH not ready yet, but instance is running${NC}"
        echo "   You may need to wait a few more minutes"
        break
    fi

    sleep 10
    echo -n "."
done
echo ""

# Step 8: Save instance information
INFO_FILE="ec2-instance-info.txt"
cat > $INFO_FILE << EOL
BodyScript EC2 Instance Information
====================================
Created: $(date)

Instance Details:
-----------------
Instance ID:     $INSTANCE_ID
Instance Type:   $INSTANCE_TYPE
Region:          $REGION
Public IP:       $PUBLIC_IP
Public DNS:      $PUBLIC_DNS
Security Group:  $SG_ID

SSH Access:
-----------
ssh -i $KEY_FILE ubuntu@$PUBLIC_IP

Deployment:
-----------
1. Update DNS record for bodyscript.andynenth.dev to point to: $PUBLIC_IP

2. Build the application:
   ./scripts/build-prod.sh

3. Deploy to EC2:
   SSH_KEY=$KEY_FILE ./scripts/deploy-ec2.sh $PUBLIC_IP

Useful Commands:
----------------
# Check instance status
aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION

# Stop instance (to save costs)
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION

# Terminate instance (permanent deletion)
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION
EOL

echo "📄 Instance information saved to: $INFO_FILE"
echo ""

# Display summary
echo "════════════════════════════════════════════"
echo "🎉 EC2 Instance Created Successfully!"
echo "════════════════════════════════════════════"
echo ""
echo "📌 Instance Details:"
echo "   ID:         $INSTANCE_ID"
echo "   Type:       $INSTANCE_TYPE"
echo "   Public IP:  ${GREEN}$PUBLIC_IP${NC}"
echo "   DNS:        $PUBLIC_DNS"
echo ""
echo "🔑 SSH Access:"
echo "   ${BLUE}ssh -i $KEY_FILE ubuntu@$PUBLIC_IP${NC}"
echo ""
echo "📝 Next Steps:"
echo "1. Update DNS for bodyscript.andynenth.dev → $PUBLIC_IP"
echo "2. Run: ${GREEN}./scripts/build-prod.sh${NC}"
echo "3. Run: ${GREEN}SSH_KEY=$KEY_FILE ./scripts/deploy-ec2.sh $PUBLIC_IP${NC}"
echo ""
echo "✨ Your EC2 instance is ready for deployment!"