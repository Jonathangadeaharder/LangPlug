#!/bin/bash
npm test -- --run --reporter=json > test-results.json 2>&1
cat test-results.json | grep -o '"fullName":"[^"]*","status":"fail"' | cut -d'"' -f4
