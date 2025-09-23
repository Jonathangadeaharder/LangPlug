#!/bin/bash

# GitHub Workflow Performance Monitoring Script
# This script provides comprehensive monitoring and analytics for GitHub workflows

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-$(gh repo view --json owner -q .owner.login)}"
REPO_NAME="${GITHUB_REPOSITORY_NAME:-$(gh repo view --json name -q .name)}"
DAYS_BACK="${DAYS_BACK:-7}"
MAX_RUNS="${MAX_RUNS:-50}"

echo -e "${BLUE}📊 GitHub Workflow Performance Dashboard${NC}"
echo -e "${BLUE}Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"
echo -e "${BLUE}Analysis period: Last ${DAYS_BACK} days${NC}"
echo "=============================================="

# Function to get workflow performance metrics
get_workflow_performance() {
    echo -e "\n${GREEN}🔍 Workflow Performance Analysis${NC}"
    echo "---------------------------------------------"

    # Get workflow runs from the last week
    gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/runs" \
        --paginate \
        --jq --arg days "$DAYS_BACK" '
        (.workflow_runs[] |
        select(.created_at | fromdateiso8601 > (now - ($days | tonumber * 86400)))) |
        {
            workflow_name: .name,
            status: .status,
            conclusion: .conclusion,
            created_at: .created_at,
            updated_at: .updated_at,
            duration: ((.updated_at | fromdateiso8601) - (.created_at | fromdateiso8601)),
            run_number: .run_number,
            head_branch: .head_branch,
            run_attempt: .run_attempt
        }' | jq -s '
        group_by(.workflow_name) |
        map({
            workflow: .[0].workflow_name,
            total_runs: length,
            successful_runs: map(select(.conclusion == "success")) | length,
            failed_runs: map(select(.conclusion == "failure")) | length,
            cancelled_runs: map(select(.conclusion == "cancelled")) | length,
            avg_duration: (map(.duration) | add / length),
            max_duration: (map(.duration) | max),
            min_duration: (map(.duration) | min),
            success_rate: ((map(select(.conclusion == "success")) | length) / length * 100)
        }) |
        sort_by(.workflow)' | \
    jq -r '
    "Workflow Name | Runs | Success% | Avg Duration | Max Duration | Failed",
    "------------- | ---- | -------- | ------------ | ------------ | ------",
    (.[] |
    "\(.workflow) | \(.total_runs) | \(.success_rate | floor)% | \(.avg_duration/60 | floor)m\(.avg_duration%60 | floor)s | \(.max_duration/60 | floor)m\(.max_duration%60 | floor)s | \(.failed_runs)")
    ' | column -t -s '|'
}

# Function to get top failing workflows
get_failing_workflows() {
    echo -e "\n${RED}❌ Top Failing Workflows${NC}"
    echo "---------------------------------------------"

    gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/runs" \
        --paginate \
        --jq --arg days "$DAYS_BACK" '
        (.workflow_runs[] |
        select(.created_at | fromdateiso8601 > (now - ($days | tonumber * 86400))) |
        select(.conclusion == "failure")) |
        {
            workflow_name: .name,
            head_branch: .head_branch,
            created_at: .created_at,
            html_url: .html_url,
            run_number: .run_number
        }' | jq -s '
        group_by(.workflow_name) |
        map({
            workflow: .[0].workflow_name,
            failure_count: length,
            recent_failures: map({run_number, head_branch, created_at}) | sort_by(.created_at) | reverse | .[0:3]
        }) |
        sort_by(.failure_count) | reverse | .[0:5]' | \
    jq -r '.[] | "❌ \(.workflow): \(.failure_count) failures"'
}

# Function to analyze job performance within workflows
get_job_performance() {
    echo -e "\n${YELLOW}⚡ Job Performance Analysis${NC}"
    echo "---------------------------------------------"

    local workflow_id
    workflow_id=$(gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows" \
        --jq '.workflows[] | select(.name == "CI") | .id' | head -1)

    if [ -n "$workflow_id" ]; then
        gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${workflow_id}/runs" \
            --jq --arg limit "$MAX_RUNS" '.workflow_runs[0:($limit | tonumber)] | .[].id' | \
        head -5 | while read -r run_id; do
            if [ -n "$run_id" ]; then
                echo "Analyzing run #$run_id..."
                gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/runs/${run_id}/jobs" \
                    --jq '.jobs[] |
                    {
                        name: .name,
                        status: .status,
                        conclusion: .conclusion,
                        duration: ((.completed_at // now | fromdateiso8601) - (.started_at | fromdateiso8601))
                    }' 2>/dev/null || echo "Could not analyze run $run_id"
            fi
        done | jq -s '
        group_by(.name) |
        map({
            job_name: .[0].name,
            avg_duration: (map(.duration) | add / length),
            runs_analyzed: length
        }) |
        sort_by(.avg_duration) | reverse' | \
        jq -r '"Job Name | Avg Duration | Samples",
               "-------- | ------------ | -------",
               (.[] | "\(.job_name) | \(.avg_duration/60 | floor)m\(.avg_duration%60 | floor)s | \(.runs_analyzed)")' | \
        column -t -s '|'
    else
        echo "Could not find CI workflow for job analysis"
    fi
}

# Function to get cache hit rates
get_cache_metrics() {
    echo -e "\n${BLUE}💾 Cache Performance${NC}"
    echo "---------------------------------------------"

    # This is a simplified version - in practice, you'd need to parse logs
    echo "Cache metrics require log analysis (not implemented in this script)"
    echo "To get cache metrics:"
    echo "1. Check workflow run logs for cache hit/miss messages"
    echo "2. Look for 'Cache restored from key:' or 'Cache not found' messages"
    echo "3. Calculate hit rate per workflow"
}

# Function to get workflow costs (billable minutes)
get_workflow_costs() {
    echo -e "\n${GREEN}💰 Workflow Costs (Billable Minutes)${NC}"
    echo "---------------------------------------------"

    # Get billing information
    gh api "repos/${REPO_OWNER}/${REPO_NAME}/settings/billing/actions" \
        --jq '
        {
            total_minutes_used: .total_minutes_used,
            total_paid_minutes_used: .total_paid_minutes_used,
            included_minutes: .included_minutes
        }' 2>/dev/null | \
    jq -r '"Total minutes used: \(.total_minutes_used)",
           "Paid minutes used: \(.total_paid_minutes_used)",
           "Included minutes: \(.included_minutes)"' || \
    echo "Billing information not available (may require admin access)"
}

# Function to get concurrent workflow usage
get_concurrent_usage() {
    echo -e "\n${YELLOW}🔄 Current Workflow Activity${NC}"
    echo "---------------------------------------------"

    gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?status=in_progress" \
        --jq '.workflow_runs |
        map({
            workflow: .name,
            status: .status,
            started: .created_at,
            branch: .head_branch
        })' | \
    jq -r 'if length > 0 then
        "Currently running workflows:",
        (.[] | "  🟡 \(.workflow) on \(.branch) (started: \(.started))")
    else
        "No workflows currently running"
    end'
}

# Function to generate trend analysis
get_trend_analysis() {
    echo -e "\n${BLUE}📈 Workflow Trends${NC}"
    echo "---------------------------------------------"

    gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/runs" \
        --paginate \
        --jq --arg days "$DAYS_BACK" '
        (.workflow_runs[] |
        select(.created_at | fromdateiso8601 > (now - ($days | tonumber * 86400)))) |
        {
            date: (.created_at | fromdateiso8601 | strftime("%Y-%m-%d")),
            workflow: .name,
            conclusion: .conclusion
        }' | jq -s '
        group_by(.date) |
        map({
            date: .[0].date,
            total_runs: length,
            success_rate: ((map(select(.conclusion == "success")) | length) / length * 100)
        }) |
        sort_by(.date)' | \
    jq -r '"Date | Total Runs | Success Rate",
           "---- | ---------- | ------------",
           (.[] | "\(.date) | \(.total_runs) | \(.success_rate | floor)%")' | \
    column -t -s '|'
}

# Function to export data for further analysis
export_data() {
    echo -e "\n${GREEN}📤 Exporting Data${NC}"
    echo "---------------------------------------------"

    local output_file="workflow-metrics-$(date +%Y%m%d-%H%M%S).json"

    gh api "repos/${REPO_OWNER}/${REPO_NAME}/actions/runs" \
        --paginate \
        --jq --arg days "$DAYS_BACK" '
        (.workflow_runs[] |
        select(.created_at | fromdateiso8601 > (now - ($days | tonumber * 86400))))' | \
    jq -s '.' > "$output_file"

    echo "Raw workflow data exported to: $output_file"
    echo "Use this file for custom analysis or import into data visualization tools"
}

# Main execution
main() {
    case "${1:-all}" in
        "performance")
            get_workflow_performance
            ;;
        "failures")
            get_failing_workflows
            ;;
        "jobs")
            get_job_performance
            ;;
        "cache")
            get_cache_metrics
            ;;
        "costs")
            get_workflow_costs
            ;;
        "concurrent")
            get_concurrent_usage
            ;;
        "trends")
            get_trend_analysis
            ;;
        "export")
            export_data
            ;;
        "all"|*)
            get_workflow_performance
            get_failing_workflows
            get_job_performance
            get_cache_metrics
            get_workflow_costs
            get_concurrent_usage
            get_trend_analysis
            echo -e "\n${GREEN}✅ Analysis Complete${NC}"
            echo "Run with specific flags for focused analysis:"
            echo "  ./workflow-performance.sh performance"
            echo "  ./workflow-performance.sh failures"
            echo "  ./workflow-performance.sh jobs"
            echo "  ./workflow-performance.sh export"
            ;;
    esac
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Run main function
main "$@"