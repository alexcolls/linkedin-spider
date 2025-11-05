#!/bin/bash
# Scale LinkedIn Spider workers

NAMESPACE="linkedin-spider"
DEPLOYMENT="linkedin-spider-worker"

# Parse arguments
REPLICAS="${1:-}"

if [ -z "$REPLICAS" ]; then
    echo "Usage: $0 <replicas>"
    echo ""
    echo "Examples:"
    echo "  $0 10      # Scale to 10 workers"
    echo "  $0 100     # Scale to 100 workers"
    echo "  $0 1000    # Scale to 1,000 workers"
    echo ""
    
    # Show current scale
    CURRENT=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null)
    if [ -n "$CURRENT" ]; then
        echo "Current replicas: $CURRENT"
        
        RUNNING=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
        echo "Running workers: $RUNNING"
    else
        echo "⚠️  Deployment not found"
    fi
    exit 1
fi

# Validate replicas is a number
if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: Replicas must be a positive number"
    exit 1
fi

# Get current replicas
CURRENT=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null)

if [ -z "$CURRENT" ]; then
    echo "❌ Error: Deployment '$DEPLOYMENT' not found in namespace '$NAMESPACE'"
    exit 1
fi

echo "📊 Scaling Workers"
echo "===================="
echo "Current replicas: $CURRENT"
echo "Target replicas:  $REPLICAS"
echo ""

# Warn for large scale
if [ "$REPLICAS" -gt 100 ]; then
    echo "⚠️  WARNING: Scaling to $REPLICAS workers will require significant resources:"
    echo "   CPU: ~$((REPLICAS / 2)) cores (requests)"
    echo "   Memory: ~$((REPLICAS))GB (requests)"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
fi

# Scale
echo "⚙️  Scaling deployment..."
kubectl scale deployment "$DEPLOYMENT" -n "$NAMESPACE" --replicas="$REPLICAS"

echo "✅ Scale command sent"
echo ""

# Watch progress
echo "📈 Watching rollout progress (Ctrl+C to exit)..."
kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=300s

echo ""
echo "🔍 Current status:"
kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker | head -20

if [ "$REPLICAS" -gt 20 ]; then
    RUNNING=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Running --no-headers | wc -l)
    echo ""
    echo "Running workers: $RUNNING/$REPLICAS"
fi
