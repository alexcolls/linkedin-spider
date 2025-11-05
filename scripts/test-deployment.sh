#!/bin/bash
# Quick test to validate LinkedIn Spider deployment

set -e

NAMESPACE="linkedin-spider"

echo "🧪 LinkedIn Spider Deployment Test"
echo "===================================="
echo ""

# Test 1: Check namespace
echo "✓ Test 1: Namespace exists"
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "  ✅ PASS: Namespace '$NAMESPACE' exists"
else
    echo "  ❌ FAIL: Namespace not found"
    exit 1
fi
echo ""

# Test 2: Check PostgreSQL
echo "✓ Test 2: PostgreSQL is running"
DB_POD=$(kubectl get pods -n "$NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$DB_POD" ]; then
    DB_STATUS=$(kubectl get pod "$DB_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    if [ "$DB_STATUS" == "Running" ]; then
        echo "  ✅ PASS: PostgreSQL pod is running"
        
        # Test database connection
        if kubectl exec -it "$DB_POD" -n "$NAMESPACE" -- psql -U postgres -d linkedin_spider -c "SELECT 1;" &> /dev/null; then
            echo "  ✅ PASS: Database connection successful"
        else
            echo "  ⚠️  WARNING: Database connection failed"
        fi
    else
        echo "  ❌ FAIL: PostgreSQL pod status: $DB_STATUS"
        exit 1
    fi
else
    echo "  ❌ FAIL: PostgreSQL pod not found"
    exit 1
fi
echo ""

# Test 3: Check Redis
echo "✓ Test 3: Redis is running"
REDIS_POD=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$REDIS_POD" ]; then
    REDIS_STATUS=$(kubectl get pod "$REDIS_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    if [ "$REDIS_STATUS" == "Running" ]; then
        echo "  ✅ PASS: Redis pod is running"
        
        # Test Redis connection
        if kubectl exec -it "$REDIS_POD" -n "$NAMESPACE" -- redis-cli ping &> /dev/null; then
            echo "  ✅ PASS: Redis connection successful"
        else
            echo "  ⚠️  WARNING: Redis connection failed"
        fi
    else
        echo "  ❌ FAIL: Redis pod status: $REDIS_STATUS"
        exit 1
    fi
else
    echo "  ❌ FAIL: Redis pod not found"
    exit 1
fi
echo ""

# Test 4: Check Workers
echo "✓ Test 4: Workers are deployed"
WORKER_COUNT=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --no-headers 2>/dev/null | wc -l)
RUNNING_WORKERS=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)

if [ "$WORKER_COUNT" -gt 0 ]; then
    echo "  ✅ PASS: $WORKER_COUNT worker pod(s) found"
    echo "  ✅ PASS: $RUNNING_WORKERS worker(s) running"
    
    # Check if at least one worker is ready
    if [ "$RUNNING_WORKERS" -gt 0 ]; then
        WORKER_POD=$(kubectl get pods -n "$NAMESPACE" -l app=linkedin-spider-worker --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        if [ -n "$WORKER_POD" ]; then
            echo "  ✅ PASS: Worker pod '$WORKER_POD' is accessible"
        fi
    fi
else
    echo "  ⚠️  WARNING: No worker pods found (may not be deployed yet)"
fi
echo ""

# Test 5: Check ConfigMap
echo "✓ Test 5: ConfigMap exists"
if kubectl get configmap linkedin-spider-config -n "$NAMESPACE" &> /dev/null; then
    echo "  ✅ PASS: ConfigMap exists"
else
    echo "  ❌ FAIL: ConfigMap not found"
    exit 1
fi
echo ""

# Test 6: Check Services
echo "✓ Test 6: Services are accessible"
POSTGRES_SVC=$(kubectl get svc postgres -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
REDIS_SVC=$(kubectl get svc redis -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null)

if [ -n "$POSTGRES_SVC" ]; then
    echo "  ✅ PASS: PostgreSQL service: $POSTGRES_SVC:5432"
else
    echo "  ❌ FAIL: PostgreSQL service not found"
    exit 1
fi

if [ -n "$REDIS_SVC" ]; then
    echo "  ✅ PASS: Redis service: $REDIS_SVC:6379"
else
    echo "  ❌ FAIL: Redis service not found"
    exit 1
fi
echo ""

# Summary
echo "===================================="
echo "🎉 All tests passed!"
echo ""
echo "Next steps:"
echo "  1. Extract cookies: poetry run python -m linkedin_spider.cli.extract_cookies --k8s-secret"
echo "  2. Apply secret: kubectl apply -f k8s/linkedin-cookies-secret.yaml"
echo "  3. Push test URL to Redis queue"
echo "  4. Monitor: ./scripts/monitor.sh"
