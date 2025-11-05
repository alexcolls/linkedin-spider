#!/bin/bash
# Setup Minikube cluster for LinkedIn Spider with sufficient resources

set -e

echo "🚀 Setting up Minikube for LinkedIn Spider..."
echo ""

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo "❌ Error: minikube is not installed"
    echo "Install from: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed"
    echo "Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Configuration
CLUSTER_NAME="${CLUSTER_NAME:-linkedin-spider}"
CPUS="${CPUS:-8}"
MEMORY="${MEMORY:-16384}"  # 16GB in MB
DISK="${DISK:-50g}"
DRIVER="${DRIVER:-docker}"

echo "📋 Configuration:"
echo "   Cluster Name: $CLUSTER_NAME"
echo "   CPUs: $CPUS"
echo "   Memory: ${MEMORY}MB ($(($MEMORY / 1024))GB)"
echo "   Disk: $DISK"
echo "   Driver: $DRIVER"
echo ""

# Check if cluster already exists
if minikube status -p "$CLUSTER_NAME" &> /dev/null; then
    echo "⚠️  Cluster '$CLUSTER_NAME' already exists"
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting existing cluster..."
        minikube delete -p "$CLUSTER_NAME"
    else
        echo "✅ Using existing cluster"
        exit 0
    fi
fi

# Start minikube
echo "🔧 Starting Minikube cluster..."
minikube start \
    -p "$CLUSTER_NAME" \
    --cpus="$CPUS" \
    --memory="$MEMORY" \
    --disk-size="$DISK" \
    --driver="$DRIVER" \
    --kubernetes-version=stable

echo ""
echo "✅ Minikube cluster started successfully!"
echo ""

# Enable addons
echo "🔌 Enabling useful addons..."
minikube addons enable metrics-server -p "$CLUSTER_NAME"
minikube addons enable dashboard -p "$CLUSTER_NAME"

echo ""
echo "📊 Cluster Information:"
kubectl cluster-info
echo ""

# Set context
kubectl config use-context "$CLUSTER_NAME"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Build Docker image: docker build -t linkedin-spider:latest ."
echo "  2. Load image to minikube: minikube image load linkedin-spider:latest -p $CLUSTER_NAME"
echo "  3. Deploy to cluster: ./scripts/deploy.sh"
echo ""
echo "Useful commands:"
echo "  - View dashboard: minikube dashboard -p $CLUSTER_NAME"
echo "  - SSH into node: minikube ssh -p $CLUSTER_NAME"
echo "  - Stop cluster: minikube stop -p $CLUSTER_NAME"
echo "  - Delete cluster: minikube delete -p $CLUSTER_NAME"
