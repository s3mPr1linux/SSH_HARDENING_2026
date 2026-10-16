#!/usr/bin/env bash
# =====================================================================
#  audit-ssh.sh — confere a configuração EFETIVA do sshd (sshd -T)
#
#  Uso:  sudo ./scripts/audit-ssh.sh            (saída colorida)
#        sudo ./scripts/audit-ssh.sh --json     (para SIEM / pipeline)
#
#  Lê o que o sshd realmente vai aplicar — não o que está escrito no
#  arquivo. É assim que se pega o drop-in do cloud-init reativando senha.
#  Código de saída = número de checagens que falharam.
# =====================================================================
set -uo pipefail

JSON=0; [[ "${1:-}" == "--json" ]] && JSON=1
[[ $EUID -eq 0 ]] || { echo "execute como root (sshd -T precisa ler as chaves de host)"; exit 2; }
command -v sshd >/dev/null || { echo "sshd não encontrado"; exit 2; }

EFFECTIVE="$(sshd -T 2>/dev/null)" || { echo "sshd -T falhou — rode 'sshd -t' para ver o erro"; exit 2; }

get() { awk -v k="$1" '$1==k {$1=""; sub(/^ /,""); print; exit}' <<<"$EFFECTIVE"; }

fails=0; results=()
SEP=$'\x1f'   # separador interno (as regex usam "|")

check() {   # check <id> <diretiva> <esperado> <descrição>
  local id="$1" key="$2" want="$3" desc="$4" got status
  got="$(get "$key")"
  if [[ "$got" == "$want" ]]; then status="PASS"; else status="FAIL"; ((fails++)); fi
  results+=("$id$SEP$status$SEP$key$SEP$want$SEP${got:-<vazio>}$SEP$desc")
}

check_max() {   # check_max <id> <diretiva> <máximo> <descrição>
  local id="$1" key="$2" max="$3" desc="$4" got status
  got="$(get "$key")"
  if [[ "$got" =~ ^[0-9]+$ ]] && (( got <= max )); then status="PASS"; else status="FAIL"; ((fails++)); fi
  results+=("$id$SEP$status$SEP$key$SEP<= $max$SEP${got:-<vazio>}$SEP$desc")
}

check_absent() {   # check_absent <id> <diretiva> <regex proibida> <descrição>
  local id="$1" key="$2" bad="$3" desc="$4" got status
  got="$(get "$key")"
  if grep -qE "$bad" <<<"$got"; then status="FAIL"; ((fails++)); else status="PASS"; fi
  results+=("$id$SEP$status$SEP$key${SEP}sem /$bad/$SEP$(cut -c1-60 <<<"$got")$SEP$desc")
}

check_set() {   # check_set <id> <diretiva> <descrição>
  local id="$1" key="$2" desc="$3" got status
  got="$(get "$key")"
  if [[ -n "$got" && "$got" != "none" ]]; then status="PASS"; else status="FAIL"; ((fails++)); fi
  results+=("$id$SEP$status$SEP$key${SEP}definido$SEP${got:-<vazio>}$SEP$desc")
}

# --- Acesso -----------------------------------------------------------
check  SSH-01 permitrootlogin             no          "Root não loga remotamente"
check  SSH-02 passwordauthentication      no          "Sem senha — somente chave"
check  SSH-03 permitemptypasswords        no          "Sem senha vazia"
check  SSH-04 pubkeyauthentication        yes         "Chave pública habilitada"
check_set SSH-05 allowgroups                          "Lista explícita de quem pode entrar"
# --- Força bruta ------------------------------------------------------
check_max SSH-06 maxauthtries 3                       "Poucas tentativas por conexão"
check_max SSH-07 logingracetime 60                    "Janela curta para autenticar"
check_set SSH-08 maxstartups                          "Limite de conexões não autenticadas"
# --- Pivô / forwarding ------------------------------------------------
check  SSH-09 x11forwarding               no          "Sem X11"
check  SSH-10 allowagentforwarding        no          "Sem agent forwarding"
check  SSH-11 allowtcpforwarding          no          "Sem túneis TCP"
check  SSH-12 permittunnel                no          "Sem tun/tap"
check  SSH-13 permituserenvironment       no          "Usuário não injeta ambiente"
# --- Sessão / log -----------------------------------------------------
check_set SSH-14 clientaliveinterval                  "Encerra sessões ociosas"
check  SSH-15 loglevel                    VERBOSE     "Loga fingerprint da chave"
# --- Criptografia -----------------------------------------------------
check_absent SSH-16 ciphers          'cbc|3des|arcfour'          "Sem cifras CBC/3DES/RC4"
check_absent SSH-17 macs             'md5|sha1|-96|(^|,)hmac-sha2-(256|512)(,|$)|(^|,)umac-(64|128)@' "Somente MACs ETM"
check_absent SSH-18 kexalgorithms    'sha1|group1-|group14-sha1|nistp' "Sem KEX SHA-1/NIST"
check_absent SSH-19 hostkeyalgorithms '(^|,)ssh-rsa(,|$)|ssh-dss|ecdsa' "Sem ssh-rsa (SHA-1)/DSA/ECDSA"

# --- Saída ------------------------------------------------------------
if (( JSON )); then
  printf '{"host":"%s","date":"%s","fails":%d,"checks":[' "$(hostname -f 2>/dev/null || hostname)" "$(date -Is)" "$fails"
  first=1
  for r in "${results[@]}"; do
    IFS="$SEP" read -r id st key want got desc <<<"$r"
    (( first )) || printf ','; first=0
    printf '{"id":"%s","status":"%s","directive":"%s","expected":"%s","found":"%s","desc":"%s"}' \
      "$id" "$st" "$key" "${want//\"/\\\"}" "${got//\"/\\\"}" "$desc"
  done
  printf ']}\n'
else
  printf '\n  %-7s %-6s %-24s %s\n' "ID" "STATUS" "DIRETIVA" "DESCRIÇÃO"
  printf '  %s\n' "-----------------------------------------------------------------------"
  for r in "${results[@]}"; do
    IFS="$SEP" read -r id st key want got desc <<<"$r"
    if [[ $st == PASS ]]; then c='\033[32m'; else c='\033[31m'; fi
    printf "  %-7s ${c}%-6s\033[0m %-24s %s\n" "$id" "$st" "$key" "$desc"
    [[ $st == FAIL ]] && printf '          esperado: %s | encontrado: %s\n' "$want" "$got"
  done
  total=${#results[@]}
  printf '\n  Resultado: %d/%d aprovados\n\n' "$((total - fails))" "$total"
fi

exit "$fails"
