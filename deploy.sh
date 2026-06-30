#!/bin/bash
# KR Campus deployment helper

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-starful-258005}"
SITE_DOMAIN="${SITE_DOMAIN:-https://krcampus.net}"
COMMIT_MSG="update: KR Campus contents $(date '+%Y-%m-%d %H:%M')"

MODE="full"
DO_GIT=false
DO_CLOUD_DEPLOY=false

print_step() { echo ""; echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BOLD}${CYAN}  $1${NC}"; echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
print_ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
print_warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
print_err()  { echo -e "${RED}  ❌ $1${NC}"; }

usage() {
    cat <<'EOF'
Usage: ./deploy.sh [MODE] [OPTIONS]

Modes
  --full           Generate content + build + seo guard (default)
  --content-only   Generate content + build only
  --deploy-only    Cloud Build deploy only

Options
  --with-git       Commit and push
  --with-deploy    Trigger deploy after mode
EOF
}

generate_content() {
    print_step "STEP A | Content generation"
    [ -f scripts/2.generate_ai_guides.py ] && python3 scripts/2.generate_ai_guides.py || print_warn "skip guides"
    [ -f scripts/1.collect_language_schools.py ] && python3 scripts/1.collect_language_schools.py || print_warn "skip language schools"
    [ -f scripts/1.collect_universities.py ] && python3 scripts/1.collect_universities.py || print_warn "skip universities"
    [ -f scripts/3.generate_japanese_native.py ] && python3 scripts/3.generate_japanese_native.py || print_warn "skip JA native"
    [ -f scripts/auto_generate_featured.py ] && python3 scripts/auto_generate_featured.py || true
    print_ok "Content generation done"
}

build_data() {
    print_step "STEP B | build_data"
    python3 scripts/build_data.py
    print_ok "build_data done"
}

seo_guard() {
    print_step "STEP C | seo_guard"
    [ -f scripts/seo_guard.py ] && python3 scripts/seo_guard.py || print_warn "skip seo_guard"
}

git_push() {
    print_step "STEP D | git push"
    git add .
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        git commit -m "$COMMIT_MSG"
        git push origin main
        print_ok "pushed"
    fi
}

deploy_cloud() {
    print_step "STEP E | Cloud Build"
    # Maps API key: cloudbuild.yaml → Secret Manager (KRCAMPUS_GOOGLE_MAPS_API_KEY)
    gcloud builds submit --project "$GCP_PROJECT_ID"
    print_ok "deploy triggered"
}

for arg in "$@"; do
    case "$arg" in
        --full) MODE="full" ;;
        --content-only) MODE="content-only" ;;
        --deploy-only) MODE="deploy-only" ;;
        --with-git) DO_GIT=true ;;
        --with-deploy) DO_CLOUD_DEPLOY=true ;;
        --help|-h) usage; exit 0 ;;
        *) echo "Unknown: $arg"; usage; exit 1 ;;
    esac
done

cd "$PROJECT_ROOT"
print_step "KR Campus deploy | $MODE | $SITE_DOMAIN"

case "$MODE" in
    full)
        generate_content
        build_data
        seo_guard
        ;;
    content-only)
        generate_content
        build_data
        ;;
    deploy-only)
        DO_CLOUD_DEPLOY=true
        ;;
esac

[ "$DO_GIT" = true ] && git_push
[ "$DO_CLOUD_DEPLOY" = true ] && deploy_cloud

print_ok "Done"
