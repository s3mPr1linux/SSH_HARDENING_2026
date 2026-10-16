# 05 — Rollback: como não se trancar para fora

## Regra de ouro

1. Mantenha **uma sessão SSH aberta** durante toda a mudança.
2. Valide com `sudo sshd -t` antes de recarregar.
3. Use `reload`, não `restart` — sessões existentes continuam vivas.
4. Teste o login em **outro terminal** antes de fechar a sessão original.

## Proteção extra: rollback automático com timer

Antes de recarregar, agende a restauração. Se você conseguir entrar de
novo, cancele o timer.

```bash
BK=$(ls -t /root/ssh-backup-*.tar.gz | head -1)
sudo systemd-run --on-active=5min --unit=ssh-rollback \
  sh -c "tar -xzf $BK -C / && systemctl reload ssh || systemctl reload sshd"

# ... aplica, testa em outro terminal, deu certo:
sudo systemctl stop ssh-rollback.timer
```

## Restaurar manualmente

```bash
sudo tar -xzf /root/ssh-backup-AAAAMMDD-HHMMSS.tar.gz -C /
sudo sshd -t && sudo systemctl reload ssh   # ou sshd
```

## Trancou mesmo?

- **VPS/nuvem:** console serial/VNC do provedor (AWS EC2 Serial Console,
  Azure Serial Console, Proxmox noVNC, Hetzner/Contabo console).
- **Físico:** console local / IPMI / iDRAC / iLO.
- Remova os drop-ins: `rm /etc/ssh/sshd_config.d/{00-hardening,10-crypto}.conf`
  e recarregue o serviço.
