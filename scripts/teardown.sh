#!/bin/bash
# Teardown LinkedIn Spider deployment from Kubernetes

NAMESPACE="linkedin-spider"

echo "🗑️  LinkedIn Spider Teardown"
echo "=============================="
echo ""

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "✅ Namespace '$NAMESPACE' does not exist. Nothing to clean up."
    exit 0
fi

# Show what will be deleted
echo "📋 Resources to be deleted:"
kubectl get all -n "$NAMESPACE"
echo ""

# Ask for confirmation
read -p "⚠️  Are you sure you want to delete ALL resources in namespace '$NAMESPACE'? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "🗑️  Deleting resources..."

# Scale down workers first for graceful shutdown
echo "1️⃣  Scaling down workers..."
kubectl scale deployment linkedin-spider-worker -n "$NAMESPACE" --replicas=0 2>/dev/null || true
sleep 5

# Delete worker deployment
echo "2️⃣  Deleting worker deployment..."
kubectl delete -f k8s/20-worker-deployment.yaml --ignore-not-found=true

# Delete network policies
echo "3️⃣  Deleting network policies..."
kubectl delete -f k8s/30-network-policy.yaml --ignore-not-found=true

# Delete Redis
echo "4️⃣  Deleting Redis..."
kubectl delete -f k8s/11-redis.yaml --ignore-not-found=true

# Delete PostgreSQL (this will also delete PVCs if cascade is enabled)
echo "5️⃣  Deleting PostgreSQL..."
kubectl delete -f k8s/10-postgres-statefulset.yaml --ignore-not-found=true

# Delete secrets and configmaps
echo "6️⃣  Deleting secrets and configmaps..."
kubectl delete -f k8s/02-secret-template.yaml --ignore-not-found=true 2>/dev/null || true
kubectl delete secret linkedin-credentials -n "$NAMESPACE" --ignore-not-found=true 2>/dev/null || true
kubectl delete -f k8s/01-configmap.yaml --ignore-not-found=true

# Wait a bit for resources to terminate
echo "⏳ Waiting for resources to terminate..."
sleep 10

# List remaining resources
REMAINING=$(kubectl get all -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  Some resources still exist:"
    kubectl get all -n "$NAMESPACE"
    echo ""
    read -p "Force delete remaining resources? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete all --all -n "$NAMESPACE" --force --grace-period=0
    fi
fi

# Delete PVCs
echo "7️⃣  Checking for PersistentVolumeClaims..."
PVCS=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
if [ "$PVCS" -gt 0 ]; then
    echo "Found $PVCS PVC(s):"
    kubectl get pvc -n "$NAMESPACE"
    echo ""
    read -p "Delete PersistentVolumeClaims? This will DELETE ALL DATA! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete pvc --all -n "$NAMESPACE"
    fi
fi

# Delete namespace
echo "8️⃣  Deleting namespace..."
read -p "Delete namespace '$NAMESPACE'? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl delete -f k8s/00-namespace.yaml
    echo "⏳ Waiting for namespace to be deleted..."
    kubectl wait --for=delete namespace/"$NAMESPACE" --timeout=120s 2>/dev/null || true
fi

echo ""
echo "✅ Teardown complete!"
echo ""

# Final check
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "⚠️  Namespace still exists. Some resources may be in terminating state."
    echo "   Check: kubectl get all -n $NAMESPACE"
else
    echo "🎉 All resources removed successfully!"
fi
