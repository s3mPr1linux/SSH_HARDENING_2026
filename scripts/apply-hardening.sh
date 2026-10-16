#!/usr/bin/env bash
# =====================================================================
#  apply-hardening.sh — aplica os drop-ins com travas de segurança
#
#  Uso:   sudo ./scripts/apply-hardening.sh [--dry-run] [--group ssh-users]
#
#  O que ele faz:
#    1. Confere OpenSSH, Include de drop-ins e se o grupo permitido
#       tem pelo menos 1 usuário com authorized_keys (evita lockout).
#    2. Faz backup de /etc/ssh.
#    3. Copia os drop-ins, regenera moduli fracos e chaves de host.
#    4. Valida com "sshd -t". Se falhar, faz rollback automático.
#    5. Recarrega (não reinicia) o serviço — sessões abertas continuam.
# =====================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_DIR="/etc/ssh"
DROPIN_DIR="${SSH_DIR}/sshd_config.d"
GROUP="ssh-users"
DRY_RUN=0
BACKUP="/root/ssh-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
info()  { printf '\033[36m[*]\033[0m %s\n' "$*"; }
die()   { red "[x] $*"; exit 1; }
run()   { if (( DRY_RUN )); then echo "    (dry-run) $*"; else "$@"; fi; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --group)   GROUP="${2:?informe o grupo}"; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) die "opção desconhecida: $1" ;;
  esac
  shift
done

[[ $EUID -eq 0 ]] || die "execute como root (sudo)."
command -v sshd >/dev/null || die "sshd não encontrado."

# --- 1. Pré-checagens -------------------------------------------------
ver="$(sshd -V 2>&1 | grep -oE 'OpenSSH_[0-9]+\.[0-9]+' | head -1 | cut -d_ -f2 || true)"
[[ -z "$ver" ]] && ver="$(ssh -V 2>&1 | grep -oE 'OpenSSH_[0-9]+\.[0-9]+' | cut -d_ -f2)"
info "OpenSSH detectado: ${ver:-desconhecido}"
if [[ -n "$ver" ]] && awk -v v="$ver" 'BEGIN{exit !(v < 8.5)}'; then
  die "OpenSSH < 8.5 — o 10-crypto.conf usa algoritmos que essa versão não conhece."
fi

grep -qE '^\s*Include\s+/etc/ssh/sshd_config\.d/\*\.conf' "${SSH_DIR}/sshd_config" \
  || die "Falta 'Include /etc/ssh/sshd_config.d/*.conf' no topo do sshd_config."

getent group "$GROUP" >/dev/null || die "Grupo '$GROUP' não existe. Crie: groupadd $GROUP && usermod -aG $GROUP <usuario>"

members="$(getent group "$GROUP" | cut -d: -f4 | tr ',' ' ')"
ok_user=""
for u in $members; do
  home="$(getent passwd "$u" | cut -d: -f6)"
  if [[ -s "${home}/.ssh/authorized_keys" ]]; then ok_user="$u"; break; fi
done
[[ -n "$ok_user" ]] || die "Nenhum membro de '$GROUP' tem ~/.ssh/authorized_keys. Você ficaria trancado para fora."
green "[+] Usuário com chave encontrado: $ok_user"

# --- 2. Backup --------------------------------------------------------
info "Backup de ${SSH_DIR} em ${BACKUP}"
run tar -czf "$BACKUP" -C / etc/ssh

rollback() {
  red "[!] Validação falhou — restaurando backup."
  run tar -xzf "$BACKUP" -C /
  exit 1
}

# --- 3. Instalação ----------------------------------------------------
run install -d -m 0755 "$DROPIN_DIR"
for f in "${REPO_DIR}"/sshd_config.d/*.conf; do
  info "Instalando $(basename "$f")"
  run install -m 0600 "$f" "${DROPIN_DIR}/$(basename "$f")"
done

if [[ ! -f /etc/issue.net ]] || ! grep -q "Acesso restrito" /etc/issue.net; then
  info "Instalando banner legal em /etc/issue.net"
  run install -m 0644 "${REPO_DIR}/templates/issue.net" /etc/issue.net
fi

info "Removendo moduli DH < 3072 bits"
if [[ -f "${SSH_DIR}/moduli" ]]; then
  run sh -c "awk '\$5 >= 3071' ${SSH_DIR}/moduli > ${SSH_DIR}/moduli.safe && mv ${SSH_DIR}/moduli.safe ${SSH_DIR}/moduli"
fi

info "Removendo chaves de host DSA/ECDSA e garantindo Ed25519 e RSA >= 3072"
run rm -f "${SSH_DIR}"/ssh_host_dsa_key* "${SSH_DIR}"/ssh_host_ecdsa_key*
[[ -f "${SSH_DIR}/ssh_host_ed25519_key" ]] || run ssh-keygen -q -t ed25519 -N '' -f "${SSH_DIR}/ssh_host_ed25519_key"
if [[ -f "${SSH_DIR}/ssh_host_rsa_key" ]]; then
  bits="$(ssh-keygen -lf "${SSH_DIR}/ssh_host_rsa_key.pub" | awk '{print $1}')"
  if (( bits < 3072 )); then
    run rm -f "${SSH_DIR}"/ssh_host_rsa_key*
    run ssh-keygen -q -t rsa -b 4096 -N '' -f "${SSH_DIR}/ssh_host_rsa_key"
  fi
else
  run ssh-keygen -q -t rsa -b 4096 -N '' -f "${SSH_DIR}/ssh_host_rsa_key"
fi

# --- 4. Validação -----------------------------------------------------
info "Validando configuração (sshd -t)"
if (( ! DRY_RUN )); then sshd -t || rollback; fi
green "[+] Configuração válida."

# --- 5. Reload --------------------------------------------------------
svc="sshd"; systemctl list-unit-files ssh.service >/dev/null 2>&1 && svc="ssh"
info "Recarregando ${svc}"
run systemctl reload "$svc" || { red "[!] reload falhou — recarregue manualmente: systemctl reload $svc"; }

green "[+] Pronto. NÃO feche esta sessão."
echo "    Teste em OUTRO terminal:  ssh -v ${ok_user}@<host>"
echo "    Depois rode:              sudo ./scripts/audit-ssh.sh"
echo "    Backup:                   ${BACKUP}"
