#!/bin/bash
# Checks that every part of the site answers with the right app.
# Usage: ./_prod_smoke.sh [base url]   (default https://ai.burn.codes)
# CURL_OPTS adds curl options, e.g. -k against a self-signed test certificate.
BASE="${1:-https://ai.burn.codes}"
failed=0

fetch() { curl -sS --max-time 20 $CURL_OPTS "$@"; }

# expect <path> <status> <text the body or Location must contain>
expect() {
  local out status body
  out=$(fetch -D - "$BASE$1") || { echo "FAIL $1: no answer"; failed=1; return; }
  status=$(printf '%s' "$out" | head -n1 | cut -d' ' -f2)
  if [ "$status" != "$2" ] || ! printf '%s' "$out" | grep -qF -- "$3"; then
    echo "FAIL $1: wanted $2 with \"$3\", got $status"
    failed=1
  else
    echo "ok   $1 ($status)"
  fi
}

# Website: real HTML, not the dashboard's empty shell
expect /            200 'data-site="burncodes"'
expect /preise/     200 'data-site="burncodes"'
expect /fr/         200 'lang="fr"'
expect /robots.txt  200 'Sitemap'
# Dashboard and the pages customers embed or share
expect /dashboard/       200 'id="app"'
expect /dashboard/login  200 'id="app"'
expect /chat/test        200 'id="app"'
# Old addresses and setup links
expect /login            301 '/dashboard/login'
expect '/?onboarding'    302 '/dashboard/?onboarding'
expect /api/health       200 ''

exit $failed
