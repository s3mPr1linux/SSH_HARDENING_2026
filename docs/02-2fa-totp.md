# 02 — 2FA: chave + TOTP

Chave pública **e** código TOTP (Google Authenticator, Aegis, 2FAS…).
Se a chave vazar, ainda falta o segundo fator.

> Prefira FIDO2 (`docs/01`) quando possível: é 2FA nativo, sem PAM.
> Use TOTP quando não houver token de hardware disponível.

## 1. Instalar

```bash
# Debian/Ubuntu
sudo apt install libpam-google-authenticator
# RHEL/Alma/Rocky (EPEL)
sudo dnf install google-authenticator qrencode
```

## 2. Registrar o usuário (como o próprio usuário, não root)

```bash
google-authenticator -t -d -f -r 3 -R 30 -w 3
```

Escaneie o QR code e **guarde os códigos de emergência** fora do servidor.

## 3. PAM — `/etc/pam.d/sshd`

Adicione no topo e **comente** a autenticação por senha, para que o
segundo fator seja o TOTP e não a senha do Linux:

```text
auth required pam_google_authenticator.so
#@include common-auth          # Debian/Ubuntu
#auth substack password-auth   # RHEL
```

## 4. sshd — edite o `00-hardening.conf`

Como no OpenSSH a **primeira ocorrência vence**, não crie outro drop-in
para isso: altere as duas linhas no próprio `00-hardening.conf`:

```text
KbdInteractiveAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
```

## 5. Validar sem se trancar

```bash
sudo sshd -t && sudo systemctl reload ssh   # ou sshd
# em OUTRO terminal:
ssh -v sl@host     # deve pedir a passphrase da chave e depois o "Verification code"
```

Se algo der errado, a sessão que ficou aberta é a sua saída.
