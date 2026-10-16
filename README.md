# SSH_HARDENING_2026

> **SSH seguro vai muito além de trocar a porta 22.**
> Configs prontas, scripts de aplicação/auditoria e documentação para
> blindar o OpenSSH em servidores Linux (Debian, Ubuntu, RHEL/Alma/Rocky).

![OpenSSH](https://img.shields.io/badge/OpenSSH-%E2%89%A5%208.5-informational)
![Linux](https://img.shields.io/badge/Debian%20%7C%20Ubuntu%20%7C%20RHEL-supported-success)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)

---

## Por que este repositório

Trocar a porta do SSH tira bots do log — e só. É segurança por obscuridade:
um `nmap -p-` encontra o serviço em segundos. O que realmente protege é a
soma de camadas:

| Camada | Controle | Onde está |
|---|---|---|
| **Identidade** | Somente chave (Ed25519/FIDO2), sem root, allowlist de grupo | `sshd_config.d/00-hardening.conf` · `docs/01` |
| **2º fator** | FIDO2 `ed25519-sk` ou chave + TOTP | `docs/01` · `docs/02` |
| **Força bruta** | `MaxAuthTries`, `MaxStartups`, Fail2Ban com ban progressivo | `00-hardening.conf` · `fail2ban/` |
| **Pivô** | Sem X11, agent forwarding, túneis | `00-hardening.conf` · `client/` |
| **Criptografia** | KEX pós-quântico híbrido, AEAD, MACs ETM, sem SHA-1 | `sshd_config.d/10-crypto.conf` |
| **Rede** | VPN/bastion, allowlist e rate limit no firewall | `docs/03` |
| **Visibilidade** | `LogLevel VERBOSE`, FIM, alertas no SIEM, auditoria de drift | `docs/04` · `scripts/audit-ssh.sh` |

## Estrutura

```text
SSH_HARDENING_2026/
├── sshd_config.d/
│   ├── 00-hardening.conf       # acesso, limites, forwarding, log
│   └── 10-crypto.conf          # algoritmos (OpenSSH >= 8.5)
├── scripts/
│   ├── apply-hardening.sh      # aplica com backup, sshd -t e rollback
│   └── audit-ssh.sh            # audita a config EFETIVA (sshd -T) — texto ou JSON
├── fail2ban/jail.d/sshd.local  # modo aggressive + ban progressivo + recidive
├── client/ssh_config.example   # hardening do lado cliente + ProxyJump
├── templates/issue.net         # banner legal
├── docs/
│   ├── 01-chaves-ed25519-fido2.md
│   ├── 02-2fa-totp.md
│   ├── 03-rede-firewall.md
│   ├── 04-monitoramento-deteccao.md
│   ├── 05-rollback.md
│   └── CHECKLIST.md
└── linkedin/                   # post + carrossel PDF de divulgação
```

## Uso rápido

> ⚠️ **Mantenha uma sessão SSH aberta** durante todo o processo e tenha
> acesso ao console do provedor. Leia [`docs/05-rollback.md`](docs/05-rollback.md).

```bash
# 0. Pré-requisitos: usuário não-root com chave funcionando
sudo groupadd -f ssh-users
sudo usermod -aG ssh-users $USER

# 1. Clonar
git clone https://github.com/s3mPr1linux/SSH_HARDENING_2026.git
cd SSH_HARDENING_2026

# 2. Simular
sudo ./scripts/apply-hardening.sh --dry-run

# 3. Aplicar (backup + validação + reload)
sudo ./scripts/apply-hardening.sh

# 4. Testar em OUTRO terminal
ssh -v $USER@servidor

# 5. Auditar
sudo ./scripts/audit-ssh.sh
```

Saída do auditor:

```text
  ID      STATUS DIRETIVA                 DESCRIÇÃO
  -----------------------------------------------------------------------
  SSH-01  PASS   permitrootlogin          Root não loga remotamente
  SSH-02  PASS   passwordauthentication   Sem senha — somente chave
  SSH-05  FAIL   allowgroups              Lista explícita de quem pode entrar
          esperado: definido | encontrado: <vazio>
  ...
  Resultado: 18/19 aprovados
```

`--json` gera saída para SIEM; o código de saída é o número de falhas
(ideal para cron/CI detectar drift).

### Fail2Ban

```bash
sudo cp fail2ban/jail.d/sshd.local /etc/fail2ban/jail.d/
sudo systemctl restart fail2ban && sudo fail2ban-client status sshd
```

## Pegadinhas que este repo trata

- **"Primeira ocorrência vence"** — o OpenSSH aplica o primeiro valor que
  lê. Por isso o prefixo `00-`: ele vence o `50-cloud-init.conf`, que em
  muitas imagens de nuvem reativa `PasswordAuthentication yes`.
- **Auditar o arquivo ≠ auditar o serviço** — `audit-ssh.sh` usa
  `sshd -T`, que mostra a configuração realmente efetiva.
- **Ubuntu 22.10+** — a porta vem do `ssh.socket`, não do `sshd_config`.
- **RHEL** — criptografia é gerida por `crypto-policies`; veja o cabeçalho
  de `10-crypto.conf`.
- **Algoritmo desconhecido derruba o sshd** — o script valida com `sshd -t`
  e faz rollback automático.

## Validação externa

```bash
pipx install ssh-audit
ssh-audit seu-servidor.com.br
```

## Referências

- Artigo que inspirou este repo: [SSH seguro além da porta — HelpSysAdmin](https://helpsysadmin.com.br/blog/ssh-seguro-alem-da-porta/)
- `man sshd_config` · `man ssh_config` · `man ssh-keygen`
- [CIS Benchmarks — Distribution Independent Linux / Ubuntu / RHEL](https://www.cisecurity.org/cis-benchmarks)
- [ssh-audit](https://github.com/jtesta/ssh-audit)
- [Mozilla OpenSSH Guidelines](https://infosec.mozilla.org/guidelines/openssh)
- MITRE ATT&CK: T1021.004 (Remote Services: SSH), T1098.004 (SSH Authorized Keys), T1110 (Brute Force)

## Aviso

Teste em laboratório antes de produção. Ajuste à sua realidade —
forwarding, SFTP e 2FA dependem do uso de cada ambiente.

---

**Autor:** Rodrigo Luz ([@s3mPr1linux](https://github.com/s3mPr1linux)) ·
[LinkedIn](https://www.linkedin.com/in/rodrigosilvaluz) ·
[Blog](https://s3mpr1linux.github.io/)

Licença [GPL-3.0](LICENSE).
