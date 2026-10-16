# 01 — Chaves: Ed25519 e FIDO2

Desligar a senha só funciona se a chave for boa e bem guardada.

## Gerar uma chave Ed25519 (padrão)

```bash
ssh-keygen -t ed25519 -a 100 -C "sl@notebook-$(date +%Y)" -f ~/.ssh/id_ed25519_vps0
```

- `-a 100` — 100 rodadas de KDF na passphrase: deixa força bruta offline cara.
- **Use passphrase.** Chave sem passphrase é senha em texto puro no disco.
- Uma chave por destino/finalidade facilita revogar sem derrubar tudo.

Se precisar de RSA por compatibilidade: `ssh-keygen -t rsa -b 4096 -a 100`.

## Enviar para o servidor

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_vps0.pub sl@vps0
```

Permissões que o sshd exige (com `StrictModes yes`, o padrão):

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## Restringir a chave no `authorized_keys`

Cada linha pode carregar opções. Ótimo para chaves de automação:

```text
from="10.0.0.0/24",no-agent-forwarding,no-port-forwarding,no-pty ssh-ed25519 AAAA... backup@ci
command="/usr/local/bin/backup-only.sh",restrict ssh-ed25519 AAAA... backup@ci
```

`restrict` desliga tudo (forwarding, pty, X11) de uma vez.

## FIDO2 / chave de hardware (YubiKey, SoloKey, etc.)

OpenSSH ≥ 8.2 suporta chaves `-sk`. A chave privada **não sai do token** e
cada login exige toque físico — phishing de chave vira impossível.

```bash
ssh-keygen -t ed25519-sk -O resident -O verify-required -C "sl@yubikey"
```

- `resident` — guarda o handle no token (dá para usar em outra máquina com `ssh-keygen -K`).
- `verify-required` — exige PIN **e** toque.

No servidor, exija verificação para chaves de hardware:

```text
PubkeyAuthOptions verify-required
```

## Escala: certificados SSH (CA)

Em frota grande, gerenciar `authorized_keys` em cada servidor não escala.
Uma CA SSH assina chaves com validade curta:

```bash
# Na CA (máquina offline/protegida)
ssh-keygen -t ed25519 -f ssh_user_ca
ssh-keygen -s ssh_user_ca -I sl@2026-10 -n sl -V +8h ~/.ssh/id_ed25519.pub
```

```text
# No servidor
TrustedUserCAKeys /etc/ssh/ssh_user_ca.pub
```

Certificado expira sozinho — sem revogação manual quando alguém sai do time.
