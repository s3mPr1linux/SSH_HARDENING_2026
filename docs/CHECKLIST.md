# Checklist de hardening SSH

Marque conforme aplica. IDs batem com o `scripts/audit-ssh.sh`.

## Checklist rápido (o mínimo)
- [ ] Login por chave SSH
- [ ] Root com senha desativado
- [ ] Usuários limitados (`AllowUsers`/`AllowGroups`)
- [ ] Fail2Ban ou CrowdSec
- [ ] Monitoramento dos acessos

O restante abaixo é o que transforma o mínimo em defesa em profundidade.

## Antes de começar
- [ ] Sessão SSH extra aberta (sua saída de emergência)
- [ ] Acesso ao console do provedor/IPMI confirmado
- [ ] Usuário não-root criado, no grupo `ssh-users` e com `sudo`
- [ ] Chave Ed25519 (com passphrase) copiada e login testado

## Identidade e acesso
- [ ] SSH-01 `PermitRootLogin no`
- [ ] SSH-02 `PasswordAuthentication no`
- [ ] SSH-03 `PermitEmptyPasswords no`
- [ ] SSH-04 `PubkeyAuthentication yes`
- [ ] SSH-05 `AllowGroups ssh-users` (ou `AllowUsers`)
- [ ] 2FA com FIDO2 (`ed25519-sk`) ou TOTP para contas privilegiadas
- [ ] `authorized_keys` revisado — nenhuma chave órfã

## Força bruta
- [ ] SSH-06 `MaxAuthTries 3`
- [ ] SSH-07 `LoginGraceTime 20`
- [ ] SSH-08 `MaxStartups 10:30:60`
- [ ] Fail2Ban (ban progressivo) **ou** CrowdSec (reputação coletiva) ativo

## Pivô e movimento lateral
- [ ] SSH-09 `X11Forwarding no`
- [ ] SSH-10 `AllowAgentForwarding no` (use `ProxyJump`)
- [ ] SSH-11 `AllowTcpForwarding no`
- [ ] SSH-12 `PermitTunnel no`
- [ ] SSH-13 `PermitUserEnvironment no`

## Criptografia
- [ ] SSH-16 Sem cifras CBC/3DES/RC4
- [ ] SSH-17 Somente MACs ETM
- [ ] SSH-18 KEX sem SHA-1 (com híbrido pós-quântico)
- [ ] SSH-19 Sem `ssh-rsa` (SHA-1), DSA e ECDSA
- [ ] Moduli DH < 3072 bits removidos
- [ ] `ssh-audit` sem itens vermelhos

## Rede
- [ ] SSH fora da internet (VPN/bastion) **ou** allowlist de origem
- [ ] Rate limit no firewall
- [ ] (opcional) Porta alterada — apenas redução de ruído

## Visibilidade
- [ ] SSH-14 `ClientAliveInterval` definido
- [ ] SSH-15 `LogLevel VERBOSE`
- [ ] Logs de auth chegando ao SIEM
- [ ] FIM em `/etc/ssh` e `authorized_keys`
- [ ] Auditoria periódica (`audit-ssh.sh --json`) com alerta em drift
