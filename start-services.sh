#!/bin/bash

# 行业信息助手 - 一键启动脚本
# 用法: ./start-services.sh [command]
# 命令: start | stop | restart | status | logs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 未运行，请先启动 Docker Desktop"
        exit 1
    fi
    log_success "Docker 运行正常"
}

# 启动中间件服务
start_services() {
    log_info "正在启动中间件服务 (PostgreSQL, Redis, Milvus, Elasticsearch)..."
    docker-compose up -d

    log_info "等待服务启动完成..."
    sleep 10

    # 检查服务状态
    check_service_health

    log_success "所有中间件服务已启动!"
    echo ""
    echo "服务访问地址:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo "  - Milvus: localhost:19530"
    echo "  - Elasticsearch: localhost:1200"
    echo "  - MinIO Console: localhost:9001 (admin/minioadmin)"
    echo ""
    log_info "现在可以启动前后端服务了"
    echo "  - 后端: cd backend && python app/app_main.py"
    echo "  - 前端: cd frontend && npm run dev"
}

# 停止服务
stop_services() {
    log_info "正在停止所有中间件服务..."
    docker-compose down
    log_success "所有服务已停止"
}

# 重启服务
restart_services() {
    stop_services
    sleep 2
    start_services
}

# 检查服务健康状态
check_service_health() {
    log_info "检查服务健康状态..."

    # PostgreSQL
    if docker exec industry_postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "PostgreSQL: 运行中"
    else
        log_warning "PostgreSQL: 启动中..."
    fi

    # Redis
    if docker exec industry_redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis: 运行中"
    else
        log_warning "Redis: 启动中..."
    fi

    # Milvus
    if curl -s http://localhost:9091/healthz > /dev/null 2>&1; then
        log_success "Milvus: 运行中"
    else
        log_warning "Milvus: 启动中..."
    fi

    # Elasticsearch
    if curl -s http://localhost:1200/_cluster/health > /dev/null 2>&1; then
        log_success "Elasticsearch: 运行中"
    else
        log_warning "Elasticsearch: 启动中..."
    fi
}

# 查看服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    echo ""
    check_service_health
}

# 查看日志
show_logs() {
    if [ -z "$2" ]; then
        docker-compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100 "$2"
    fi
}

# 清理数据（危险操作）
clean_data() {
    log_warning "警告: 此操作将删除所有数据，包括数据库、缓存和向量数据!"
    read -p "确定要继续吗? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        stop_services
        docker-compose down -v
        log_success "所有数据已清理"
    else
        log_info "操作已取消"
    fi
}

# 显示帮助
show_help() {
    echo "行业信息助手 - 服务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动所有中间件服务"
    echo "  stop     停止所有服务"
    echo "  restart  重启所有服务"
    echo "  status   查看服务状态"
    echo "  logs     查看服务日志 (可选: logs [服务名])"
    echo "  clean    清理所有数据 (危险!)"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动服务"
    echo "  $0 logs postgres  # 查看 PostgreSQL 日志"
}

# 主逻辑
case "$1" in
    start)
        check_docker
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        check_docker
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    clean)
        clean_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
