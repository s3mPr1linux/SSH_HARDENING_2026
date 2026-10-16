# 06 — CrowdSec: a alternativa moderna ao Fail2Ban

| | Fail2Ban | CrowdSec |
|---|---|---|
| Decide com base em | logs **deste** servidor | logs deste servidor **+ reputação coletiva** |
| Bot distribuído (1 tentativa por IP) | passa despercebido | IPs já conhecidos são bloqueados antes de tentar |
| Ação | regra local de firewall | *bouncer* (firewall, nginx, Cloudflare…) |
| Simplicidade | muito simples, estável | um pouco mais de peças |
| Melhor para | servidor interno, pouco tráfego | VPS e servidores expostos à internet |

Use **um ou outro** para o SSH — os dois banindo o mesmo IP só gera ruído.

## Instalação (Debian/Ubuntu/RHEL)

```bash
# repositório oficial
curl -s https://install.crowdsec.net | sudo sh

# Debian/Ubuntu
sudo apt install crowdsec crowdsec-firewall-bouncer-nftables
# RHEL/Alma/Rocky
sudo dnf install crowdsec crowdsec-firewall-bouncer-nftables
```

> Usa iptables? Troque o bouncer por `crowdsec-firewall-bouncer-iptables`.

## Garantir o cenário de SSH

```bash
sudo cscli collections install crowdsecurity/sshd
sudo systemctl reload crowdsec

sudo cscli collections list | grep sshd      # instalado?
sudo cscli metrics                           # os logs do sshd estão sendo lidos?
```

## Operação do dia a dia

```bash
sudo cscli decisions list                    # quem está bloqueado agora
sudo cscli alerts list                       # o que disparou
sudo cscli decisions delete --ip 203.0.113.10   # desbanir
```

## Não se bloqueie

Coloque sua origem de gestão em allowlist
(`/etc/crowdsec/parsers/s02-enrich/mywhitelists.yaml`):

```yaml
name: crowdsecurity/whitelists-local
description: "Origens de administração"
whitelist:
  reason: "admin"
  ip:
    - "203.0.113.10"
  cidr:
    - "10.8.0.0/24"
```

```bash
sudo systemctl reload crowdsec
```

## Opcional: Console

Registrar a instância no CrowdSec Console (`cscli console enroll <token>`)
dá painel web e alertas, e é o que permite receber blocklists adicionais.
