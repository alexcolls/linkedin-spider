#!/bin/bash
# Deploy LinkedIn Spider to Kubernetes cluster

set -e

echo "🚀 Deploying LinkedIn Spider to Kubernetes..."
echo ""

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: kubectl is not configured or cluster is not accessible"
    exit 1
fi

# Configuration
NAMESPACE="linkedin-spider"
WORKER_REPLICAS="${WORKER_REPLICAS:-10}"  # Start with 10 for testing
IMAGE_NAME="linkedin-spider:latest"

echo "📋 Deployment Configuration:"
echo "   Namespace: $NAMESPACE"
echo "   Worker Replicas: $WORKER_REPLICAS"
echo "   Image: $IMAGE_NAME"
echo ""

# Check if Docker image exists in minikube
read -p "Have you loaded the Docker image to minikube? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  Please load the image first:"
    echo "   docker build -t $IMAGE_NAME ."
    echo "   minikube image load $IMAGE_NAME"
    exit 1
fi

# Apply manifests in order
echo "📦 Applying Kubernetes manifests..."
echo ""

# 1. Namespace
echo "Creating namespace..."
kubectl apply -f k8s/00-namespace.yaml

# 2. ConfigMap
echo "Creating ConfigMap..."
kubectl apply -f k8s/01-configmap.yaml

# 3. Secret (check if exists)
if [ -f "k8s/linkedin-cookies-secret.yaml" ]; then
    echo "Creating Secret (LinkedIn cookies)..."
    kubectl apply -f k8s/linkedin-cookies-secret.yaml
else
    echo "⚠️  Warning: k8s/linkedin-cookies-secret.yaml not found"
    echo "   Workers will run without authenticated sessions"
    echo "   Generate it with: poetry run python -m linkedin_spider.cli.extract_cookies --k8s-secret"
    echo ""
fi

# 4. PostgreSQL StatefulSet
echo "Deploying PostgreSQL..."
kubectl apply -f k8s/10-postgres-statefulset.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s

# 5. Redis
echo "Deploying Redis..."
kubectl apply -f k8s/11-redis.yaml

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=120s

# 6. Update worker replicas in deployment
echo "Configuring worker replicas to $WORKER_REPLICAS..."
kubectl apply -f k8s/20-worker-deployment.yaml
kubectl scale deployment linkedin-spider-worker -n "$NAMESPACE" --replicas="$WORKER_REPLICAS"

# 7. Network Policies
echo "Applying network policies..."
kubectl apply -f k8s/30-network-policy.yaml

echo ""
echo "✅ Deployment complete!"
echo ""

# Show status
echo "📊 Cluster Status:"
kubectl get pods -n "$NAMESPACE"
echo ""

# Show services
echo "🌐 Services:"
kubectl get services -n "$NAMESPACE"
echo ""

echo "Next steps:"
echo "  1. Check pod status: kubectl get pods -n $NAMESPACE"
echo "  2. View logs: kubectl logs -f -n $NAMESPACE -l app=linkedin-spider-worker"
echo "  3. Push URLs to queue (see README-K8S.md)"
echo "  4. Scale workers: kubectl scale deployment linkedin-spider-worker -n $NAMESPACE --replicas=100"
echo ""
echo "Database access:"
echo "  kubectl exec -it postgres-0 -n $NAMESPACE -- psql -U postgres -d linkedin_spider"
echo ""
echo "Monitor deployment:"
echo "  ./scripts/monitor.sh"
