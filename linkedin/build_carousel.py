#!/usr/bin/env python3
"""Gera linkedin/carousel.pdf (1080x1350, um slide por página).
Uso: python3 linkedin/build_carousel.py   (requer: pip install playwright && playwright install chromium)
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
HANDLE = "@s3mPr1linux"
REPO = "github.com/s3mPr1linux/SSH_HARDENING_2026"


def code(lines):
    """Bloco de terminal. Linhas: str simples, ou ('cmt'|'ok'|'bad'|'dim'|'key', texto)."""
    out = []
    for ln in lines:
        if isinstance(ln, tuple):
            cls, txt = ln
            out.append(f'<span class="{cls}">{txt}</span>')
        else:
            out.append(ln)
    body = "\n".join(out)
    return f'''<div class="term"><div class="term-bar"><i></i><i></i><i></i></div><pre>{body}</pre></div>'''


def kv(k, v):
    return f'<span class="key">{k}</span> <span class="val">{v}</span>'


SLIDES = []

# 1 — capa
SLIDES.append(dict(kind="cover", html=f'''
<div class="kicker">Hardening OpenSSH · 2026</div>
<h1 class="mega">Mudei a porta<br>do SSH.<br><span class="accent">Estou seguro?</span></h1>
<p class="lead">Spoiler: não. Você só ficou mais silencioso.<br>
Arraste para ver as 7 camadas que realmente protegem →</p>
{code([("dim", "$ grep Port /etc/ssh/sshd_config"), "Port 49222", ("bad", "# isso sozinho não é segurança")])}
'''))

# 2 — problema
SLIDES.append(dict(title="O problema", html=f'''
<h2>Trocar a porta é <span class="accent">obscuridade</span>, não controle.</h2>
<p>Ela tira o ruído dos bots do <code>auth.log</code> — e isso tem valor.
Mas quem mira no <b>seu</b> servidor faz isto:</p>
{code([("dim", "$ nmap -sV -p- --min-rate 5000 alvo"),
       "PORT      STATE SERVICE VERSION",
       ("bad", "49222/tcp open  ssh     OpenSSH 9.6p1"),
       ("dim", "# encontrado. próxima etapa: credenciais.")])}
<div class="callout">Reduz <b>ruído</b>. Não reduz <b>risco</b>. Use como bônus — nunca como a defesa.</div>
'''))

# 3 — camadas
layers = [
    ("01", "Identidade", "só chave, sem root, allowlist"),
    ("02", "Chaves fortes", "Ed25519 · FIDO2 · 2FA"),
    ("03", "Força bruta", "limites + Fail2Ban / CrowdSec"),
    ("04", "Pivô", "sem forwarding, use ProxyJump"),
    ("05", "Criptografia", "KEX pós-quântico, sem SHA-1"),
    ("06", "Rede", "VPN / bastion / allowlist"),
    ("07", "Visibilidade", "logs, FIM, drift no SIEM"),
]
rows = "".join(f'<div class="layer"><span class="n">{n}</span><b>{t}</b><span class="d">{d}</span></div>' for n, t, d in layers)
SLIDES.append(dict(title="O mapa", html=f'''
<h2>SSH seguro é <span class="accent">soma de camadas</span>.</h2>
<p>Se uma falhar, a próxima segura. Nenhuma depende do número da porta.</p>
<div class="layers">{rows}</div>
'''))

# 4 — identidade
SLIDES.append(dict(title="01 · Identidade", html=f'''
<h2>Quem entra — e <span class="accent">como</span>.</h2>
{code([("cmt", "# /etc/ssh/sshd_config.d/00-hardening.conf"),
       kv("PermitRootLogin", "no"),
       kv("PasswordAuthentication", "no"),
       kv("KbdInteractiveAuthentication", "no"),
       kv("AuthenticationMethods", "publickey"),
       kv("AllowGroups", "ssh-users")])}
<ul>
<li><b>Sem senha</b> = força bruta de senha vira inútil.</li>
<li><b>Sem root</b> = o atacante precisa adivinhar o usuário <i>e</i> escalar.</li>
<li><b>AllowGroups</b> = conta de serviço esquecida não loga por SSH.</li>
</ul>
'''))

# 5 — chaves
SLIDES.append(dict(title="02 · Chaves fortes", html=f'''
<h2>Desligar senha só funciona com <span class="accent">chave boa</span>.</h2>
{code([("cmt", "# padrão: Ed25519 com KDF reforçado + passphrase"),
       "$ ssh-keygen -t ed25519 -a 100",
       "",
       ("cmt", "# melhor: chave de hardware FIDO2 (PIN + toque)"),
       "$ ssh-keygen -t ed25519-sk \\", "    -O resident -O verify-required"])}
<ul>
<li>A chave FIDO2 <b>não sai do token</b>: roubar o arquivo não basta.</li>
<li>Sem token? Chave + <b>TOTP</b> via PAM.</li>
<li>Frota grande? <b>Certificados SSH</b> com validade de horas.</li>
</ul>
'''))

# 6 — força bruta
SLIDES.append(dict(title="03 · Força bruta", html=f'''
<h2>Menos tentativas, <span class="accent">menos janela</span>.</h2>
{code([kv("MaxAuthTries", "3"),
       kv("LoginGraceTime", "20"),
       kv("MaxStartups", "10:30:60"),
       kv("ClientAliveInterval", "300"),
       "",
       ("cmt", "# /etc/fail2ban/jail.d/sshd.local"),
       kv("mode", "= aggressive"),
       kv("bantime.increment", "= true"),
       ("cmt", "# reincidente: 1h → 2h → 4h … até 1 semana")])}
<p class="small">Exposto à internet? <b>CrowdSec</b> soma reputação coletiva e pega bot distribuído. Com senha desligada, ambos viram <b>redução de ruído + telemetria</b> para o SIEM.</p>
'''))

# 7 — pivô
SLIDES.append(dict(title="04 · Pivô", html=f'''
<h2>Seu servidor não pode virar <span class="accent">trampolim</span>.</h2>
{code([kv("X11Forwarding", "no"),
       kv("AllowAgentForwarding", "no"),
       kv("AllowTcpForwarding", "no"),
       kv("PermitTunnel", "no"),
       kv("PermitUserEnvironment", "no")])}
<div class="callout"><b>Agent forwarding</b> deixa quem tem root no servidor usar <i>sua</i> chave.
Para saltar entre hosts, use <code>ProxyJump</code>: o bastion nunca toca na sua chave.</div>
{code([("dim", "$ ssh -J bastion servidor-interno")])}
'''))

# 8 — cripto
SLIDES.append(dict(title="05 · Criptografia", html=f'''
<h2>Algoritmos de <span class="accent">2026</span>, não de 2006.</h2>
{code([("cmt", "# 10-crypto.conf (OpenSSH ≥ 8.5)"),
       kv("KexAlgorithms", "sntrup761x25519-sha512@openssh.com,"),
       "  curve25519-sha256,…",
       kv("Ciphers", "chacha20-poly1305@openssh.com,"),
       "  aes256-gcm@openssh.com,…",
       kv("MACs", "hmac-sha2-512-etm@openssh.com,…"),
       kv("HostKeyAlgorithms", "ssh-ed25519,rsa-sha2-512,…")])}
<ul>
<li><b>sntrup761</b>: híbrido pós-quântico contra "grave agora, decifre depois".</li>
<li>Fora: CBC, SHA-1, <code>ssh-rsa</code>, DSA/ECDSA, moduli &lt; 3072.</li>
<li>Confira de fora com <code>ssh-audit</code>.</li>
</ul>
'''))

# 9 — pegadinha
SLIDES.append(dict(title="⚠ A pegadinha", html=f'''
<h2>O OpenSSH usa a <span class="accent">primeira</span> ocorrência.</h2>
<p>Em imagens de nuvem, o cloud-init pode religar a senha sem você ver:</p>
{code([("dim", "$ ls /etc/ssh/sshd_config.d/"),
       ("ok", "00-hardening.conf  "),
       ("bad", "50-cloud-init.conf  # PasswordAuthentication yes"),
       "",
       ("cmt", "# não audite o arquivo. audite o serviço:"),
       ("dim", "$ sudo sshd -T | grep passwordauthentication"),
       ("ok", "passwordauthentication no")])}
<div class="callout">Prefixo <b>00-</b> faz o seu drop-in vencer. <code>sshd -T</code> mostra a config <b>efetiva</b>.</div>
'''))

# 10 — rede + visibilidade
SLIDES.append(dict(title="06 + 07 · Rede e visibilidade", html=f'''
<h2>A melhor porta é a que <span class="accent">ninguém alcança</span>.</h2>
<ul>
<li><b>Rede:</b> SSH atrás de VPN ou bastion. Se exposto, allowlist + rate limit no firewall.</li>
</ul>
{code([kv("LogLevel", "VERBOSE"),
       ("dim", "Accepted publickey for sl from 203.0.113.10"),
       ("dim", "  ssh2: ED25519 SHA256:k3y…  ← qual chave entrou")])}
<p class="small"><b>Alerte no SIEM:</b></p>
<ul class="tight">
<li>mudança em <code>authorized_keys</code> → persistência (ATT&amp;CK T1098.004)</li>
<li>fingerprint fora do inventário · login de origem nova</li>
<li><code>sshd -T</code> com senha ligada → drift</li>
</ul>
'''))

# 11 — não se tranque
SLIDES.append(dict(title="Antes de aplicar", html=f'''
<h2>Hardening que te tranca <span class="accent">para fora</span> é incidente.</h2>
<div class="steps">
<div><span>1</span><em>Mantenha uma sessão SSH <b>aberta</b>.</em></div>
<div><span>2</span><em>Valide com <code>sshd -t</code> antes de tudo.</em></div>
<div><span>3</span><em>Use <code>reload</code>, não <code>restart</code>.</em></div>
<div><span>4</span><em>Teste o login em <b>outro</b> terminal.</em></div>
<div><span>5</span><em>Tenha o console do provedor à mão.</em></div>
</div>
{code([("cmt", "# rede de segurança: rollback sozinho em 5 min"),
       "$ systemd-run --on-active=5min --unit=ssh-rollback …",
       ("ok", "$ systemctl stop ssh-rollback.timer   # deu certo")])}
'''))

# 12 — CTA
SLIDES.append(dict(kind="cta", html=f'''
<div class="kicker">Repositório aberto</div>
<h2 class="big">Tudo isso pronto para usar.</h2>
{code([("dim", "$ sudo ./scripts/apply-hardening.sh"),
       ("ok", "[+] Configuração válida."),
       ("dim", "$ sudo ./scripts/audit-ssh.sh"),
       ("ok", "Resultado: 19/19 aprovados")])}
<ul>
<li>Drop-ins para <code>sshd_config.d/</code> + Fail2Ban + cliente</li>
<li>Aplicação com backup, validação e rollback</li>
<li>Auditor de 19 checagens — texto ou JSON p/ SIEM</li>
<li>Docs: FIDO2, 2FA, firewall, detecção, checklist</li>
</ul>
<div class="repo">{REPO}</div>
<p class="small">Qual camada ainda falta no seu ambiente? Comenta aí 👇<br>
<span class="muted">Base: "SSH seguro além de mudar a porta" — HelpSysAdmin</span></p>
'''))

CSS = """
@page { size: 1080px 1350px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0b0f14; --panel: #111821; --line: #1f2a37;
  --fg: #e6edf3; --muted: #8b98a8; --accent: #3ddc84; --amber: #ffb84d; --red: #ff6b6b; --cyan: #5cc8ff;
}
html, body { background: var(--bg); }
body { font-family: 'Inter', 'DejaVu Sans', sans-serif; color: var(--fg); }
.slide {
  width: 1080px; height: 1350px; position: relative; overflow: hidden;
  padding: 150px 84px 140px; page-break-after: always;
  background:
    radial-gradient(900px 600px at 110% -10%, rgba(61,220,132,.10), transparent 60%),
    linear-gradient(transparent 0 0) , var(--bg);
}
.slide::before { /* grade sutil */
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background-image: linear-gradient(var(--line) 1px, transparent 1px), linear-gradient(90deg, var(--line) 1px, transparent 1px);
  background-size: 54px 54px; opacity: .22;
  mask-image: linear-gradient(180deg, #000 0%, transparent 55%);
}
.top { position: absolute; top: 56px; left: 84px; right: 84px; display: flex; justify-content: space-between; align-items: center;
  font-family: 'DejaVu Sans Mono', monospace; font-size: 22px; color: var(--muted); }
.top .tag { color: var(--accent); }
.foot { position: absolute; bottom: 56px; left: 84px; right: 84px; display: flex; justify-content: space-between; align-items: center;
  font-family: 'DejaVu Sans Mono', monospace; font-size: 22px; color: var(--muted); }
.foot .swipe { color: var(--accent); }
.bar { position: absolute; bottom: 0; left: 0; height: 8px; background: var(--accent); }
.content { position: relative; display: flex; flex-direction: column; gap: 34px; height: 100%; justify-content: center; }
.section { font-family: 'DejaVu Sans Mono', monospace; font-size: 26px; color: var(--accent); letter-spacing: .04em; text-transform: uppercase; }
.kicker { font-family: 'DejaVu Sans Mono', monospace; font-size: 26px; color: var(--accent); letter-spacing: .08em; text-transform: uppercase; }
h1.mega { font-size: 112px; line-height: 1.0; font-weight: 800; letter-spacing: -0.03em; }
h2 { font-size: 64px; line-height: 1.08; font-weight: 800; letter-spacing: -0.02em; }
h2.big { font-size: 76px; }
.accent { color: var(--accent); }
p { font-size: 32px; line-height: 1.45; color: #c9d4df; }
p.lead { font-size: 36px; }
p.small { font-size: 28px; }
.muted { color: var(--muted); font-size: 24px; }
b { color: var(--fg); font-weight: 700; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: .86em; color: var(--amber);
  background: rgba(255,184,77,.08); padding: 2px 10px; border-radius: 8px; }
ul { list-style: none; display: flex; flex-direction: column; gap: 18px; }
ul li { font-size: 30px; line-height: 1.4; color: #c9d4df; padding-left: 40px; position: relative; }
ul li::before { content: "▸"; position: absolute; left: 0; color: var(--accent); }
ul.tight { gap: 10px; } ul.tight li { font-size: 27px; }
.term { background: var(--panel); border: 1px solid var(--line); border-radius: 20px; overflow: hidden;
  box-shadow: 0 30px 60px rgba(0,0,0,.35); }
.term-bar { height: 44px; display: flex; gap: 10px; align-items: center; padding-left: 20px; border-bottom: 1px solid var(--line); background: #0e141c; }
.term-bar i { width: 14px; height: 14px; border-radius: 50%; background: #2b3746; display: block; }
.term-bar i:first-child { background: #ff5f56; } .term-bar i:nth-child(2) { background: #ffbd2e; } .term-bar i:nth-child(3) { background: #27c93f; }
pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 27px; line-height: 1.55; padding: 26px 30px; color: var(--fg); white-space: pre-wrap; word-break: break-word; }
pre .key { color: var(--cyan); } pre .val { color: var(--accent); }
pre .cmt { color: #6a7a8c; font-style: italic; } pre .dim { color: var(--muted); }
pre .ok { color: var(--accent); } pre .bad { color: var(--red); }
.callout { border-left: 6px solid var(--amber); background: rgba(255,184,77,.07); padding: 24px 30px; border-radius: 0 16px 16px 0;
  font-size: 30px; line-height: 1.45; color: #e9dcc6; }
.layers { display: flex; flex-direction: column; gap: 14px; }
.layer { display: grid; grid-template-columns: 90px 300px 1fr; align-items: center; background: var(--panel); border: 1px solid var(--line);
  border-radius: 16px; padding: 22px 28px; font-size: 30px; }
.layer .n { font-family: 'DejaVu Sans Mono', monospace; color: var(--accent); font-size: 28px; }
.layer .d { color: var(--muted); font-size: 26px; }
.steps { display: flex; flex-direction: column; gap: 16px; }
.steps div { font-size: 32px; display: flex; align-items: center; gap: 24px; color: #c9d4df; }
.steps em { font-style: normal; }
.steps span { flex: 0 0 56px; height: 56px; border-radius: 50%; background: var(--accent); color: #06210f; font-weight: 800;
  display: flex; align-items: center; justify-content: center; font-size: 28px; }
.repo { font-family: 'DejaVu Sans Mono', monospace; font-size: 30px; color: #06210f; background: var(--accent);
  padding: 22px 28px; border-radius: 14px; font-weight: 700; text-align: center; }
.cover h1 { margin-top: 10px; }
"""


def render():
    total = len(SLIDES)
    pages = []
    for i, s in enumerate(SLIDES, 1):
        kind = s.get("kind", "")
        section = f'<div class="section">{s["title"]}</div>' if s.get("title") else ""
        swipe = "arraste →" if i < total else "salve ★ · compartilhe ↻"
        pages.append(f'''
<section class="slide {kind}">
  <div class="top"><span class="tag">~/SSH_HARDENING_2026</span><span>{i:02d}/{total:02d}</span></div>
  <div class="content">{section}{s["html"]}</div>
  <div class="foot"><span>{HANDLE} · Rodrigo Luz</span><span class="swipe">{swipe}</span></div>
  <div class="bar" style="width:{i/total*100:.1f}%"></div>
</section>''')
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'
    (HERE / "carousel.html").write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.set_content(html, wait_until="networkidle")
        pg.pdf(path=str(HERE / "carousel.pdf"), width="1080px", height="1350px", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        # checagem de overflow: conteúdo não pode invadir rodapé
        over = pg.evaluate("""() => [...document.querySelectorAll('.slide')].map((s,i)=>{
            const c=s.querySelector('.content'); return {i:i+1, h:c.scrollHeight, max:c.clientHeight};
        }).filter(x=>x.h>x.max)""")
        b.close()
    print("overflow:", over or "nenhum")


if __name__ == "__main__":
    render()
