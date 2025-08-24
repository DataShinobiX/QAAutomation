#!/bin/bash

# Database Inspector Script for QA Automation Platform
# Usage: ./scripts/db_inspector.sh [command]

DB_CONTAINER="qa_postgres"
DB_USER="qa_user" 
DB_NAME="qa_automation"

# Function to execute SQL commands
run_sql() {
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "$1"
}

case "${1:-help}" in
    "help")
        echo "🔍 Database Inspector Commands:"
        echo ""
        echo "  ./scripts/db_inspector.sh summary     - Show database overview"
        echo "  ./scripts/db_inspector.sh analyses    - List all website analyses"  
        echo "  ./scripts/db_inspector.sh latest      - Show latest analysis details"
        echo "  ./scripts/db_inspector.sh count       - Count records in all tables"
        echo "  ./scripts/db_inspector.sh schema      - Show table schemas"
        echo "  ./scripts/db_inspector.sh json [ID]   - Show full JSON for analysis ID"
        echo "  ./scripts/db_inspector.sh performance - Show performance metrics"
        echo ""
        ;;
    
    "summary")
        echo "📊 Database Summary"
        echo "=================="
        run_sql "SELECT 
            'website_analyses' as table_name, COUNT(*) as records 
            FROM website_analyses
        UNION ALL SELECT 
            'test_cases' as table_name, COUNT(*) as records 
            FROM test_cases
        UNION ALL SELECT 
            'test_executions' as table_name, COUNT(*) as records 
            FROM test_executions;"
        ;;
        
    "analyses")
        echo "🌐 All Website Analyses"
        echo "======================"
        run_sql "SELECT 
            LEFT(id::text, 8) || '...' as short_id,
            url,
            analysis_data->>'page_title' as title,
            created_at
        FROM website_analyses 
        ORDER BY created_at DESC;"
        ;;
        
    "latest")
        echo "📋 Latest Analysis Details"
        echo "========================="
        run_sql "SELECT 
            id,
            url,
            analysis_data->>'page_title' as title,
            analysis_data->'performance_metrics'->>'load_time_ms' as load_time_ms,
            jsonb_array_length(analysis_data->'links') as link_count,
            jsonb_array_length(analysis_data->'form_elements') as form_count,
            created_at
        FROM website_analyses 
        ORDER BY created_at DESC 
        LIMIT 1;"
        ;;
        
    "count")
        echo "📈 Record Counts"
        echo "==============="
        run_sql "SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_tuples
        FROM pg_stat_user_tables 
        WHERE tablename IN ('website_analyses', 'test_cases', 'test_executions');"
        ;;
        
    "schema")
        echo "🏗️  Table Schemas"
        echo "================"
        for table in website_analyses test_cases test_executions; do
            echo ""
            echo "--- $table ---"
            run_sql "\d $table"
        done
        ;;
        
    "json")
        if [ -z "$2" ]; then
            echo "❌ Please provide an analysis ID"
            echo "Usage: ./scripts/db_inspector.sh json [analysis_id]"
            exit 1
        fi
        echo "📄 Full JSON for Analysis: $2"
        echo "================================"
        run_sql "SELECT jsonb_pretty(analysis_data) FROM website_analyses WHERE id = '$2';"
        ;;
        
    "performance")
        echo "⚡ Performance Metrics"
        echo "===================="
        run_sql "SELECT 
            analysis_data->>'url' as url,
            (analysis_data->'performance_metrics'->>'load_time_ms')::int as load_time_ms,
            analysis_data->>'page_title' as title,
            created_at
        FROM website_analyses 
        WHERE analysis_data->'performance_metrics' IS NOT NULL
        ORDER BY (analysis_data->'performance_metrics'->>'load_time_ms')::int DESC;"
        ;;
        
    *)
        echo "❌ Unknown command: $1"
        echo "Run './scripts/db_inspector.sh help' for available commands"
        exit 1
        ;;
esac