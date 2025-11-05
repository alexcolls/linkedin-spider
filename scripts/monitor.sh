#!/bin/bash
# Monitor LinkedIn Spider deployment in Kubernetes

NAMESPACE="linkedin-spider"

echo "📊 LinkedIn Spider - Cluster Monitoring"
echo "========================================"
echo ""

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to cluster"
    exit 1
fi

# Namespace status
echo "🏷️  Namespace:"
kubectl get namespace "$NAMESPACE" 2>/dev/null || echo "❌ Namespace not found"
echo ""

# Pods status
echo "🔷 Pods Status:"
kubectl get pods -n "$NAMESPACE" -o wide
echo ""

# Worker statistics
TOTAL_WORKERS=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --no-headers 2>/dev/null | wc -l)
RUNNING_WORKERS=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
PENDING_WORKERS=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Pending --no-headers 2>/dev/null | wc -l)
FAILED_WORKERS=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l)

echo "⚙️  Worker Statistics:"
echo "   Total: $TOTAL_WORKERS"
echo "   Running: $RUNNING_WORKERS"
echo "   Pending: $PENDING_WORKERS"
echo "   Failed: $FAILED_WORKERS"
echo ""

# Database status
echo "💾 Database:"
DB_POD=$(kubectl get pods -n "$NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$DB_POD" ]; then
    DB_STATUS=$(kubectl get pod "$DB_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    echo "   Pod: $DB_POD"
    echo "   Status: $DB_STATUS"
    
    # Get profile count
    if [ "$DB_STATUS" == "Running" ]; then
        PROFILE_COUNT=$(kubectl exec -it "$DB_POD" -n "$NAMESPACE" -- psql -U postgres -d linkedin_spider -t -c "SELECT COUNT(*) FROM profiles;" 2>/dev/null | tr -d ' \n\r')
        echo "   Profiles: ${PROFILE_COUNT:-0}"
    fi
else
    echo "   ❌ Database pod not found"
fi
echo ""

# Redis status
echo "📨 Redis Queue:"
REDIS_POD=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$REDIS_POD" ]; then
    REDIS_STATUS=$(kubectl get pod "$REDIS_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    echo "   Pod: $REDIS_POD"
    echo "   Status: $REDIS_STATUS"
    
    # Get queue size
    if [ "$REDIS_STATUS" == "Running" ]; then
        QUEUE_SIZE=$(kubectl exec -it "$REDIS_POD" -n "$NAMESPACE" -- redis-cli ZCARD linkedin:urls 2>/dev/null | tr -d '\r')
        DEAD_LETTER=$(kubectl exec -it "$REDIS_POD" -n "$NAMESPACE" -- redis-cli ZCARD linkedin:urls:dead 2>/dev/null | tr -d '\r')
        echo "   Queue Size: ${QUEUE_SIZE:-0}"
        echo "   Dead Letters: ${DEAD_LETTER:-0}"
    fi
else
    echo "   ❌ Redis pod not found"
fi
echo ""

# Resource usage (if metrics-server is enabled)
echo "📈 Resource Usage:"
if kubectl top nodes &> /dev/null; then
    kubectl top pods -n "$NAMESPACE" --containers 2>/dev/null | head -20
else
    echo "   ⚠️  Metrics not available (enable metrics-server addon)"
fi
echo ""

# Services
echo "🌐 Services:"
kubectl get services -n "$NAMESPACE"
echo ""

# Recent events
echo "📋 Recent Events:"
kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
echo ""

echo "========================================"
echo "Refresh: watch -n 5 ./scripts/monitor.sh"
echo "Live logs: kubectl logs -f -n $NAMESPACE -l app=linkedin-spider-worker --tail=20"
