#!/usr/bin/env bash
# =============================================================================
# deploy_all.sh — Operation Piggy Bank 2026
# Purpose : Orchestrate deployment from CONTROL machine (your laptop/PC)
#           to multiple Orange Pi 5 boards over SSH.
#
# Modes:
#   --phase 1          Deploy only to currently ACTIVE_NODES in config.env
#   --phase 2          Deploy to next batch (boards 5-6) — rolling
#   --nodes 1 2 3 4    Deploy to specific node numbers only
#   --rolling-prepare  Gracefully stop 2 nodes before rolling in next 2
#   --status           Show service status across all active nodes
#   --update           Pull latest binaries only (no config change)
#
# Usage examples:
#   bash deploy_all.sh --phase 1
#   bash deploy_all.sh --nodes 1 2
#   bash deploy_all.sh --rolling-prepare --shutdown 1 2 --bringup 5 6
#   bash deploy_all.sh --status
#
# SECURITY DISCLAIMER: I am not a security auditor.
#   Review before running. Keep SSH keys secure.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.env"

# ---------- Color helpers ----------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---------- SSH helper -------------------------------------------------------
# Usage: remote_exec NODE_NUM "command"
remote_exec() {
    local node="$1"; shift
    local node_ip_var="NODE_${node}_IP"
    local node_ip="${!node_ip_var}"
    ssh -i "${SSH_KEY_PATH}" \
        -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=10 \
        -o BatchMode=yes \
        -p "${SSH_PORT}" \
        "${SSH_USER}@${node_ip}" "$@"
}

# Usage: remote_copy NODE_NUM local_file remote_path
remote_copy() {
    local node="$1"
    local local_file="$2"
    local remote_path="$3"
    local node_ip_var="NODE_${node}_IP"
    local node_ip="${!node_ip_var}"
    scp -i "${SSH_KEY_PATH}" \
        -o StrictHostKeyChecking=accept-new \
        -o BatchMode=yes \
        -P "${SSH_PORT}" \
        "$local_file" \
        "${SSH_USER}@${node_ip}:${remote_path}"
}

# ---------- Resolve target nodes from arguments ------------------------------
DEPLOY_NODES=()    # nodes to deploy to
SHUTDOWN_NODES=()  # nodes to stop (rolling)
BRINGUP_NODES=()   # nodes to start (rolling)
ACTION="deploy"

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --phase)
                if [[ "$2" == "1" ]]; then
                    # Active nodes from config.env
                    read -ra DEPLOY_NODES <<< "$ACTIVE_NODES"
                elif [[ "$2" == "2" ]]; then
                    # Phase 2 = nodes 5 and 6 (rolling)
                    DEPLOY_NODES=(5 6)
                else
                    error "--phase must be 1 or 2"; exit 1
                fi
                shift 2
                ;;
            --nodes)
                shift
                while [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; do
                    DEPLOY_NODES+=("$1"); shift
                done
                ;;
            --rolling-prepare)
                ACTION="rolling"
                shift
                ;;
            --shutdown)
                shift
                while [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; do
                    SHUTDOWN_NODES+=("$1"); shift
                done
                ;;
            --bringup)
                shift
                while [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; do
                    BRINGUP_NODES+=("$1"); shift
                done
                ;;
            --status)
                ACTION="status"
                read -ra DEPLOY_NODES <<< "$ACTIVE_NODES"
                shift
                ;;
            --update)
                ACTION="update"
                read -ra DEPLOY_NODES <<< "$ACTIVE_NODES"
                shift
                ;;
            *)
                error "Unknown argument: $1"
                echo "Usage: $0 --phase 1|2 | --nodes N... | --rolling-prepare --shutdown N... --bringup N... | --status | --update"
                exit 1
                ;;
        esac
    done

    if [[ ${#DEPLOY_NODES[@]} -eq 0 && "$ACTION" != "rolling" && "$ACTION" != "status" && "$ACTION" != "update" ]]; then
        warn "No nodes specified. Defaulting to ACTIVE_NODES from config.env: ${ACTIVE_NODES}"
        read -ra DEPLOY_NODES <<< "$ACTIVE_NODES"
    fi
}
parse_args "$@"

# ---------- Pre-flight: verify SSH connectivity ------------------------------
preflight_ssh() {
    local nodes=("$@")
    info "Pre-flight: testing SSH connectivity to ${#nodes[@]} node(s)..."
    local failed=0
    for n in "${nodes[@]}"; do
        local ip_var="NODE_${n}_IP"
        local ip="${!ip_var}"
        if ssh -i "${SSH_KEY_PATH}" -o BatchMode=yes -o ConnectTimeout=8 \
               -p "${SSH_PORT}" "${SSH_USER}@${ip}" true 2>/dev/null; then
            success "Node ${n} (${ip}) — reachable"
        else
            error "Node ${n} (${ip}) — NOT reachable via SSH"
            failed=$((failed+1))
        fi
    done
    if [[ $failed -gt 0 ]]; then
        error "${failed} node(s) unreachable. Aborting."
        exit 1
    fi
    success "All target nodes reachable."
}

# ---------- Deploy a single node ---------------------------------------------
deploy_node() {
    local node="$1"
    local role_var="NODE_${node}_ROLE"
    local role="${!role_var:-miner}"

    info "Deploying Node ${node} as role: ${role}"

    # Upload scripts and config
    info "  [${node}] Uploading scripts..."
    remote_exec "$node" "mkdir -p /opt/piggybank"
    remote_copy "$node" "${SCRIPT_DIR}/config.env"             "/opt/piggybank/config.env"
    remote_copy "$node" "${SCRIPT_DIR}/00_base_hardening.sh"   "/opt/piggybank/"
    remote_copy "$node" "${SCRIPT_DIR}/01_install_fullnode.sh" "/opt/piggybank/"
    remote_copy "$node" "${SCRIPT_DIR}/02_install_miner.sh"    "/opt/piggybank/"
    remote_exec "$node" "chmod +x /opt/piggybank/*.sh"

    # Run hardening
    info "  [${node}] Running hardening..."
    remote_exec "$node" "bash /opt/piggybank/00_base_hardening.sh --node ${node}"

    # Run role-specific install
    if [[ "$role" == "fullnode" ]]; then
        info "  [${node}] Installing fullnode..."
        remote_exec "$node" "bash /opt/piggybank/01_install_fullnode.sh"
    else
        info "  [${node}] Installing miner..."
        remote_exec "$node" "bash /opt/piggybank/02_install_miner.sh --node ${node}"
    fi

    success "Node ${node} deployed successfully."
}

# ---------- Status check for a node -----------------------------------------
check_status() {
    local node="$1"
    local role_var="NODE_${node}_ROLE"
    local role="${!role_var:-miner}"
    local ip_var="NODE_${node}_IP"
    local ip="${!ip_var}"

    if [[ "$role" == "fullnode" ]]; then
        local unit="${SYSTEMD_FULLNODE_UNIT}"
    else
        local unit="${SYSTEMD_MINER_UNIT}"
    fi

    local status
    status=$(remote_exec "$node" "systemctl is-active ${unit} 2>/dev/null || echo 'inactive'")
    echo -e "  Node ${node} (${ip}) [${role}] — service ${unit}: ${BOLD}${status}${NC}"

    # Also show last 3 log lines
    remote_exec "$node" "tail -3 ${LOG_DIR}/${role/fullnode/full}.log 2>/dev/null || true" | \
        sed "s/^/    [log] /"
}

# ---------- Rolling deployment helper ----------------------------------------
do_rolling() {
    if [[ ${#SHUTDOWN_NODES[@]} -eq 0 && ${#BRINGUP_NODES[@]} -eq 0 ]]; then
        error "--rolling-prepare requires --shutdown N... and --bringup N..."
        echo "  Example: --rolling-prepare --shutdown 1 2 --bringup 5 6"
        exit 1
    fi

    if [[ ${#SHUTDOWN_NODES[@]} -gt 0 ]]; then
        preflight_ssh "${SHUTDOWN_NODES[@]}"
        info "Rolling step 1: Gracefully stopping nodes ${SHUTDOWN_NODES[*]}..."
        for n in "${SHUTDOWN_NODES[@]}"; do
            local role_var="NODE_${n}_ROLE"
            local role="${!role_var:-miner}"
            if [[ "$role" == "fullnode" ]]; then
                remote_exec "$n" "systemctl stop ${SYSTEMD_FULLNODE_UNIT} && systemctl disable ${SYSTEMD_FULLNODE_UNIT}"
            else
                remote_exec "$n" "systemctl stop ${SYSTEMD_MINER_UNIT} && systemctl disable ${SYSTEMD_MINER_UNIT}"
            fi
            success "Node ${n} stopped."
        done
        echo ""
        warn ">>> Physically swap boards now: bring online nodes ${BRINGUP_NODES[*]} <<<"
        echo ""
        read -rp "Press ENTER when new boards are powered on and reachable..."
    fi

    if [[ ${#BRINGUP_NODES[@]} -gt 0 ]]; then
        preflight_ssh "${BRINGUP_NODES[@]}"
        info "Rolling step 2: Deploying to new nodes ${BRINGUP_NODES[*]}..."
        for n in "${BRINGUP_NODES[@]}"; do
            deploy_node "$n"
        done
        success "Rolling deployment complete. New nodes: ${BRINGUP_NODES[*]}"
    fi
}

# ---------- Update binaries only (no config change) --------------------------
do_update() {
    info "Updating Hacash binaries to ${HACASH_VERSION} on nodes: ${DEPLOY_NODES[*]}"
    preflight_ssh "${DEPLOY_NODES[@]}"
    for n in "${DEPLOY_NODES[@]}"; do
        local role_var="NODE_${n}_ROLE"
        local role="${!role_var:-miner}"
        info "Updating Node ${n} (${role})..."
        remote_exec "$n" "systemctl stop ${SYSTEMD_FULLNODE_UNIT} ${SYSTEMD_MINER_UNIT} 2>/dev/null || true"
        if [[ "$role" == "fullnode" ]]; then
            remote_exec "$n" "curl -fsSL --retry 3 '${GITHUB_RELEASE_BASE}/${FULLNODE_BINARY}' -o '${INSTALL_DIR}/hacash_fullnode' && chmod +x '${INSTALL_DIR}/hacash_fullnode'"
            remote_exec "$n" "systemctl start ${SYSTEMD_FULLNODE_UNIT}"
        else
            remote_exec "$n" "curl -fsSL --retry 3 '${GITHUB_RELEASE_BASE}/${POWORKER_BINARY}' -o '${INSTALL_DIR}/hacash_poworker' && chmod +x '${INSTALL_DIR}/hacash_poworker'"
            remote_exec "$n" "systemctl start ${SYSTEMD_MINER_UNIT}"
        fi
        success "Node ${n} updated."
    done
}

# ---------- MAIN -------------------------------------------------------------
echo ""
echo -e "${BOLD}=============================================="
echo " Operation Piggy Bank 2026 — Deploy All"
echo " Action      : ${ACTION}"
echo " Target nodes: ${DEPLOY_NODES[*]:-n/a}"
echo -e "==============================================${NC}"
echo ""

case "$ACTION" in
    deploy)
        preflight_ssh "${DEPLOY_NODES[@]}"
        for n in "${DEPLOY_NODES[@]}"; do
            deploy_node "$n"
            echo ""
        done
        echo ""
        success "==== Deployment complete for nodes: ${DEPLOY_NODES[*]} ===="
        ;;
    rolling)
        do_rolling
        ;;
    status)
        preflight_ssh "${DEPLOY_NODES[@]}"
        echo ""
        info "Service status across active nodes:"
        for n in "${DEPLOY_NODES[@]}"; do
            check_status "$n"
        done
        ;;
    update)
        do_update
        ;;
esac
