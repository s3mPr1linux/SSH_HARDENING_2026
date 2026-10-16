# 03 — Rede: o SSH não precisa estar aberto para a internet

A melhor porta SSH é a que o atacante não alcança.

## Ordem de preferência

1. **Sem SSH público** — acesso por VPN (WireGuard/Tailscale) ou bastion.
2. **Allowlist de origem** no firewall (IP fixo de casa/empresa).
3. **Rate limit** no firewall + Fail2Ban/CrowdSec.
4. Trocar a porta — **só redução de ruído**, nunca a única medida.

## nftables — allowlist + rate limit

```nft
table inet filter {
  set ssh_admins {
    type ipv4_addr; flags interval
    elements = { 203.0.113.10, 10.8.0.0/24 }
  }

  chain input {
    type filter hook input priority 0; policy drop;
    ct state established,related accept
    iif lo accept

    # SSH só para quem está na allowlist, no máximo 4 novas conexões/min por IP
    tcp dport 22 ip saddr @ssh_admins ct state new \
      meter ssh_rl { ip saddr limit rate 4/minute } accept
    tcp dport 22 counter drop
  }
}
```

## UFW (atalho)

```bash
sudo ufw allow from 203.0.113.10 to any port 22 proto tcp
sudo ufw limit 22/tcp        # 6 conexões / 30 s por IP
```

## Trocando a porta (se for trocar)

1. Libere a nova porta no firewall **antes**.
2. Debian/RHEL: `Port 49222` no `00-hardening.conf`.
3. **Ubuntu 22.10+** usa socket activation — a porta vem do `ssh.socket`:

```bash
sudo systemctl edit ssh.socket
# [Socket]
# ListenStream=
# ListenStream=49222
sudo systemctl daemon-reload && sudo systemctl restart ssh.socket
```

4. RHEL com SELinux: `sudo semanage port -a -t ssh_port_t -p tcp 49222`.
5. Evite 2222/22222 — já estão nas wordlists dos scanners.

## Port knocking / SPA

Para quem quer ir além: `fwknop` (Single Packet Authorization) mantém a
porta fechada até receber um pacote assinado. Útil em VPS exposta, mas
VPN costuma ser mais simples de operar.
