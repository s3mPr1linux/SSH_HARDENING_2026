# 00 — Primeiro acesso: usuário sudo + chave, sem se trancar

Antes de aplicar qualquer drop-in deste repo, você precisa de um usuário
não-root que entre **por chave**. Esta é a sequência segura, na ordem.

> Mantenha uma janela aberta como root durante **todas** as etapas.

## 1. Criar o usuário administrativo

```bash
ssh root@IP_DO_SERVIDOR

useradd -m -s /bin/bash nomeusuario
passwd nomeusuario

# Debian/Ubuntu
usermod -aG sudo nomeusuario
# AlmaLinux/Rocky/RHEL
usermod -aG wheel nomeusuario

# grupo usado pelo AllowGroups deste repo
groupadd -f ssh-users
usermod -aG ssh-users nomeusuario

# diretório da chave com as permissões que o sshd exige
install -d -m 700 -o nomeusuario -g nomeusuario /home/nomeusuario/.ssh
```

## 2. Gerar a chave no SEU computador

Prefira Ed25519; use RSA 4096 só se algum sistema antigo exigir.

```bash
ssh-keygen -t ed25519 -a 100 -C "nomeusuario@dominio.com" -f ~/.ssh/nomeusuario
# compatibilidade:
# ssh-keygen -t rsa -b 4096 -a 100 -C "nomeusuario@dominio.com" -f ~/.ssh/nomeusuario
```

**Coloque passphrase.** Funciona igual no PowerShell do Windows 10/11
(OpenSSH nativo); a chave fica em `C:\Users\<voce>\.ssh\`.

## 3. Enviar a chave pública

Linux/macOS:

```bash
ssh-copy-id -i ~/.ssh/nomeusuario.pub nomeusuario@IP_DO_SERVIDOR
```

Windows (PowerShell — não tem `ssh-copy-id`):

```powershell
type $env:USERPROFILE\.ssh\nomeusuario.pub | ssh nomeusuario@IP_DO_SERVIDOR "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

## 4. Testar o login por chave (em OUTRA janela)

```bash
ssh -i ~/.ssh/nomeusuario nomeusuario@IP_DO_SERVIDOR
sudo -v     # confirma que o sudo funciona
```

Só siga em frente se **as duas coisas** funcionaram.

## 5. Agora sim: desligar senha e root

```bash
git clone https://github.com/s3mPr1linux/SSH_HARDENING_2026.git
cd SSH_HARDENING_2026
sudo ./scripts/apply-hardening.sh --dry-run
sudo ./scripts/apply-hardening.sh
```

O script se recusa a continuar se nenhum membro de `ssh-users` tiver
`authorized_keys` — é a mesma trava do passo 4, automatizada.

Prefere fazer à mão? A ordem é a mesma do artigo de referência: deixe
`PasswordAuthentication yes` até o login por chave funcionar, **depois**
mude para `no` e recarregue com `systemctl reload ssh` (ou `sshd`).

## Root: `no` ou `prohibit-password`?

| Valor | Efeito | Quando usar |
|---|---|---|
| `no` (padrão deste repo) | root não entra por SSH de forma alguma | o normal: admin entra com usuário próprio e usa `sudo` |
| `prohibit-password` | root entra **só por chave** | automação legada que precisa de root direto (backup, Ansible antigo) |

`no` dá rastreabilidade: o log mostra **quem** entrou antes de virar root.
