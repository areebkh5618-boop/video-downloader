#!/usr/bin/env bash
# Simple validation script for Phase 8
set -euo pipefail

echo "▶ AreebFetch validation"

# Check required tools
command -v docker >/dev/null 2>&1 || { echo "docker required"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "curl required"; exit 1; }

echo "✓ Tools present"

# Backend health (if running)
if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
  echo "✓ Backend health endpoint responding"
  curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || true
else
  echo "ℹ Backend not running (start with: docker compose up -d)"
fi

# Frontend
if curl -sf http://localhost:3000 >/dev/null 2>&1; then
  echo "✓ Frontend responding"
else
  echo "ℹ Frontend not running"
fi

echo "▶ Validation finished"