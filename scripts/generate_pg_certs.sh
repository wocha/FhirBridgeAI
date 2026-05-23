#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${ROOT_DIR}/certs"
CRT_FILE="${CERT_DIR}/pg-server.crt"
KEY_FILE="${CERT_DIR}/pg-server.key"
DAYS="${PG_CERT_DAYS:-825}"
CN="${PG_CERT_CN:-postgres}"

mkdir -p "${CERT_DIR}"

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout "${KEY_FILE}" -out "${CRT_FILE}" \
  -days "${DAYS}" -subj "/CN=${CN}" \
  -addext "subjectAltName=DNS:${CN},DNS:localhost"

chmod 600 "${KEY_FILE}" || true
chmod 644 "${CRT_FILE}" || true

echo "Generated PostgreSQL TLS certificate: ${CRT_FILE}"
echo "Generated PostgreSQL TLS private key: ${KEY_FILE}"
