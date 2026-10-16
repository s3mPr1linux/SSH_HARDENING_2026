# 04 — Monitoramento: hardening sem visibilidade é aposta

Com `LogLevel VERBOSE`, cada login registra **qual chave** foi usada:

```text
sshd[1234]: Accepted publickey for sl from 203.0.113.10 port 51122 ssh2: ED25519 SHA256:abc...
```

Isso permite responder "quem entrou?" mesmo quando várias pessoas usam a
mesma conta de serviço.

## Em tempo real

```bash
journalctl -u ssh -u sshd -f      # Debian/Ubuntu usam "ssh"; RHEL usa "sshd"
```

Para histórico e alertas sem SIEM, Zabbix, Netdata, Prometheus
(node_exporter + Loki) ou HetrixTools já resolvem bem em VPS.

## Consultas rápidas

```bash
# Logins aceitos hoje
journalctl -u ssh -u sshd --since today | grep -E "Accepted (publickey|keyboard)"

# Top 10 IPs com falha
journalctl -u ssh -u sshd --since "24 hours ago" \
  | grep -oP '(?<=from )[\d.]+' | sort | uniq -c | sort -rn | head

# Fingerprints das chaves autorizadas (para cruzar com os logs)
for f in /home/*/.ssh/authorized_keys /root/.ssh/authorized_keys; do
  [ -f "$f" ] && echo "== $f" && ssh-keygen -lf "$f"
done
```

## O que alertar no SIEM (Wazuh / Elastic / Sentinel)

| Sinal | Por que importa |
|---|---|
| Login aceito de IP/país nunca visto para o usuário | Chave roubada ou credencial reutilizada |
| Login aceito com fingerprint que não está no inventário | Chave plantada no `authorized_keys` (persistência — T1098.004) |
| Alteração em `authorized_keys` ou `/etc/ssh/` | Persistência / desarme do hardening |
| `sshd -T` com `passwordauthentication yes` | Drift de configuração (cloud-init, automação, alguém "consertando") |
| Muitos `Invalid user` seguidos de um `Accepted` do mesmo IP | Força bruta que deu certo |
| Sessão SSH saindo de um servidor para outro interno | Movimento lateral (T1021.004) |

## Integridade de arquivos

Monitore com FIM (Wazuh syscheck, AIDE, auditd):

```text
/etc/ssh/
/root/.ssh/authorized_keys
/home/*/.ssh/authorized_keys
/etc/pam.d/sshd
```

Regra auditd mínima:

```bash
-w /etc/ssh/ -p wa -k sshd_config
-w /root/.ssh/ -p wa -k ssh_keys_root
```

## Auditoria contínua

Rode `scripts/audit-ssh.sh --json` via cron/timer e envie a saída ao SIEM:
o código de saída é o número de falhas, então qualquer valor > 0 é drift.

Externamente, `ssh-audit <host>` mostra o que um atacante enxerga.
