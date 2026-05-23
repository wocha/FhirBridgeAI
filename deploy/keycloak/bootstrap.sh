#!/usr/bin/env bash
set -euo pipefail

KCADM_BIN="/opt/keycloak/bin/kcadm.sh"
KC_URL="${KEYCLOAK_BOOTSTRAP_URL:-https://keycloak.docker.localhost}"
REALM="${KEYCLOAK_REALM:-FhirBridgeAI}"
OIDC_CLIENT_ID="${KEYCLOAK_OIDC_CLIENT_ID:-streamlit-dashboard}"
KC_CA_CERT_PATH="${KEYCLOAK_BOOTSTRAP_CA_CERT_PATH:-/etc/ssl/certs/local-ca.pem}"
KC_TRUSTSTORE_PATH="${KEYCLOAK_BOOTSTRAP_TRUSTSTORE_PATH:-/tmp/keycloak-bootstrap-truststore.p12}"
KC_TRUSTSTORE_PASSWORD="${KEYCLOAK_BOOTSTRAP_TRUSTSTORE_PASSWORD:-changeit}"
KCADM_KC_OPTS=""

require_env() {
  local var_name="$1"
  local value="${!var_name:-}"
  if [[ -z "$value" ]]; then
    echo "[bootstrap] missing required env: ${var_name}" >&2
    exit 1
  fi
}

require_file() {
  local file_path="$1"
  if [[ ! -f "$file_path" ]]; then
    echo "[bootstrap] required file not found: ${file_path}" >&2
    exit 1
  fi
}

run_kcadm() {
  if [[ -n "${KCADM_KC_OPTS}" ]]; then
    KC_OPTS="${KCADM_KC_OPTS} ${KC_OPTS:-}" "${KCADM_BIN}" "$@"
  else
    "${KCADM_BIN}" "$@"
  fi
}

require_env "KEYCLOAK_ADMIN"
require_env "KEYCLOAK_ADMIN_PASSWORD"
require_env "OAUTH2_PROXY_CLIENT_SECRET"

if [[ "${OAUTH2_PROXY_CLIENT_SECRET}" == "CHANGE_ME" ]]; then
  echo "[bootstrap] OAUTH2_PROXY_CLIENT_SECRET must not be CHANGE_ME" >&2
  exit 1
fi

if [[ "${KC_URL}" =~ ^http:// ]]; then
  echo "[bootstrap] insecure KEYCLOAK_BOOTSTRAP_URL is forbidden. Use HTTPS endpoint." >&2
  exit 1
fi

if [[ "${KC_URL}" =~ ^https:// ]]; then
  require_file "${KC_CA_CERT_PATH}"
  rm -f "${KC_TRUSTSTORE_PATH}"
  keytool -importcert -noprompt \
    -storetype PKCS12 \
    -alias local-ca \
    -file "${KC_CA_CERT_PATH}" \
    -keystore "${KC_TRUSTSTORE_PATH}" \
    -storepass "${KC_TRUSTSTORE_PASSWORD}" >/dev/null

  KCADM_KC_OPTS="-Djavax.net.ssl.trustStore=${KC_TRUSTSTORE_PATH} -Djavax.net.ssl.trustStorePassword=${KC_TRUSTSTORE_PASSWORD}"
  echo "[bootstrap] TLS truststore prepared for CA validation"
fi

echo "[bootstrap] authenticating against ${KC_URL}"
run_kcadm config credentials \
  --server "${KC_URL}" \
  --realm master \
  --user "${KEYCLOAK_ADMIN}" \
  --password "${KEYCLOAK_ADMIN_PASSWORD}"

CLIENT_UUID="$(run_kcadm get clients -r "${REALM}" -q clientId="${OIDC_CLIENT_ID}" --fields id --format csv --noquotes | head -n1)"
if [[ -z "${CLIENT_UUID}" ]]; then
  echo "[bootstrap] oidc client '${OIDC_CLIENT_ID}' not found in realm '${REALM}'" >&2
  exit 1
fi

run_kcadm update "clients/${CLIENT_UUID}" -r "${REALM}" -s "secret=${OAUTH2_PROXY_CLIENT_SECRET}"
echo "[bootstrap] client secret updated for '${OIDC_CLIENT_ID}'"

MAPPER_NAME="aud-mapper-${OIDC_CLIENT_ID}"
if ! run_kcadm get "clients/${CLIENT_UUID}/protocol-mappers/models" -r "${REALM}" --fields name --format csv --noquotes | grep -Fxq "${MAPPER_NAME}"; then
  run_kcadm create "clients/${CLIENT_UUID}/protocol-mappers/models" -r "${REALM}" \
    -s "name=${MAPPER_NAME}" \
    -s "protocol=openid-connect" \
    -s "protocolMapper=oidc-audience-mapper" \
    -s "consentRequired=false" \
    -s "config.\"included.client.audience\"=${OIDC_CLIENT_ID}" \
    -s "config.\"id.token.claim\"=true" \
    -s "config.\"access.token.claim\"=true"
  echo "[bootstrap] audience mapper '${MAPPER_NAME}' created"
else
  echo "[bootstrap] audience mapper '${MAPPER_NAME}' already present"
fi

upsert_user() {
  local username="$1"
  local password="$2"
  local role="$3"
  local email="$4"

  if [[ -z "${username}" ]]; then
    return 0
  fi

  if [[ -z "${password}" || "${password}" == "CHANGE_ME" ]]; then
    echo "[bootstrap] password missing/invalid for user '${username}'" >&2
    exit 1
  fi

  local user_id
  user_id="$(run_kcadm get users -r "${REALM}" -q username="${username}" --fields id --format csv --noquotes | head -n1)"

  if [[ -z "${user_id}" ]]; then
    local create_args=("create" "users" "-r" "${REALM}" "-s" "username=${username}" "-s" "enabled=true")
    if [[ -n "${email}" ]]; then
      create_args+=("-s" "email=${email}" "-s" "emailVerified=true")
    fi
    run_kcadm "${create_args[@]}"
    user_id="$(run_kcadm get users -r "${REALM}" -q username="${username}" --fields id --format csv --noquotes | head -n1)"
    echo "[bootstrap] created user '${username}'"
  fi

  if [[ -n "${email}" ]]; then
    run_kcadm update "users/${user_id}" -r "${REALM}" -s "email=${email}" -s "emailVerified=true" -s "requiredActions=[]"
  else
    run_kcadm update "users/${user_id}" -r "${REALM}" -s "emailVerified=true" -s "requiredActions=[]"
  fi

  run_kcadm set-password -r "${REALM}" --username "${username}" --new-password "${password}"
  run_kcadm add-roles -r "${REALM}" --uusername "${username}" --rolename "${role}" >/dev/null 2>&1 || true
  echo "[bootstrap] ensured role '${role}' for '${username}' and set bootstrap password"
}

upsert_user \
  "${KEYCLOAK_BOOTSTRAP_AUDITOR_USER:-}" \
  "${KEYCLOAK_BOOTSTRAP_AUDITOR_PASSWORD:-}" \
  "auditor" \
  "${KEYCLOAK_BOOTSTRAP_AUDITOR_EMAIL:-}"

upsert_user \
  "${KEYCLOAK_BOOTSTRAP_VIEWER_USER:-}" \
  "${KEYCLOAK_BOOTSTRAP_VIEWER_PASSWORD:-}" \
  "viewer" \
  "${KEYCLOAK_BOOTSTRAP_VIEWER_EMAIL:-}"

echo "[bootstrap] keycloak bootstrap completed"
