Mudei a porta do SSH para 49222. Estou seguro?

Não. Você só ficou mais silencioso.

Trocar a porta tira o ruído dos bots do auth.log — e isso tem valor. Mas um `nmap -p-` acha o serviço em segundos, e quem está mirando no SEU servidor não usa a mesma wordlist do bot.

SSH seguro de verdade é soma de camadas:

🔑 Identidade — somente chave (Ed25519 ou FIDO2), sem root, allowlist de grupo
🛡️ Força bruta — MaxAuthTries, LoginGraceTime e Fail2Ban ou CrowdSec
🚫 Pivô — sem agent forwarding, X11 e túneis (use ProxyJump)
🔐 Criptografia — KEX híbrido pós-quântico, AEAD, MACs ETM, adeus ssh-rsa/SHA-1
🌐 Rede — VPN/bastion ou allowlist no firewall
👁️ Visibilidade — LogLevel VERBOSE, FIM no authorized_keys e alerta de drift no SIEM

E uma pegadinha que pega muita gente em nuvem: o OpenSSH aplica a PRIMEIRA ocorrência de cada diretiva. Aquele 50-cloud-init.conf pode estar religando `PasswordAuthentication yes` sem você saber. Não audite o arquivo — audite o serviço com `sshd -T`.

Transformei isso num repositório aberto:
✅ drop-ins prontos para /etc/ssh/sshd_config.d/
✅ script de aplicação com backup, `sshd -t` e rollback automático
✅ auditor com 19 checagens (texto ou JSON para SIEM, exit code = drift)
✅ Fail2Ban e CrowdSec, config de cliente (inclusive Windows), 2FA, firewall e checklist

No lab: de 7/19 para 19/19 aprovados, login por chave OK, root e senha negados, KEX SHA-1 recusado.

📎 Carrossel com o passo a passo no post
🔗 Repo: github.com/s3mPr1linux/SSH_HARDENING_2026

A base é o ótimo guia "SSH seguro além de mudar a porta", do HelpSysAdmin: chave no lugar de senha, root bloqueado, AllowUsers, Fail2Ban/CrowdSec e monitoramento. Peguei cada passo dele, versionei, automatizei e somei FIDO2, criptografia pós-quântica, bloqueio de pivô e detecção no SIEM.

E aí, qual dessas camadas ainda falta no seu ambiente? 👇

#CyberSecurity #Linux #SSH #Hardening #BlueTeam #SysAdmin #SOC #InfoSec #DevSecOps #SegurançaDaInformação
