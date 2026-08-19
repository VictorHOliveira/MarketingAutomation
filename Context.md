# Context.md - Marketing Automation Project

## Resumo

Sistema automatizado de marketing orgânico para 4 projetos, com foco em máxima automação e trabalho manual mínimo. Usando APIs diretas (PowerShell) e automação de browser (Node.js + Puppeteer) para publicação em Dev.to, LinkedIn e Reddit.

---

## Projetos

| Projeto | Descrição | URL | Stack |
|---|---|---|---|
| **QA Overflow** | Blog técnico de QA e Automação de Testes | https://qaoverflow.com | Static site |
| **ScanDoc** | Antivírus para documentos - detecta prompt injection | https://scandoc.qaoverflow.com | Python/FastAPI + React + Firebase |
| **SuperTarefas** | App gamificado para tarefas domésticas infantis | Play Store (com.supertarefas.app) | Flutter + Firebase |
| **QA Picker** | Extensão Chrome para extrair seletores CSS/XPath | Chrome Web Store | JavaScript |

---

## Canais Ativos

| Canal | Status | Método de Publicação |
|---|---|---|
| **Dev.to** | ✅ Funcionando | PowerShell + API REST |
| **LinkedIn** | ✅ Funcionando | PowerShell + API REST |
| **Reddit** | ✅ Funcionando | Node.js + Puppeteer CDP + API |
| **Twitter/X** | ❌ Desativado | Opcional (pago) |
| **Canva** | ✅ Funcionando | OAuth + Python |
| **OpenAI** | ❌ Não utilizado | - |
| **Medium** | ⏳ Pendente | Importação manual |

---

## Credenciais Configuradas

### Dev.to
- API Key: `***REDACTED***`
- Username: `victorholiveira`

### LinkedIn
- Client ID: `***REDACTED***`
- Client Secret: `***REDACTED***`
- Access Token: Salvo em `output/linkedin_token.json`
- Person URN: `urn:li:person:c6v72cAYZL`

### Reddit
- Client ID: `***REDACTED***`
- Client Secret: `***REDACTED***`
- Username: `scandoc_dev`
- Password: `***REDACTED***`
- Método: Automação via browser (não API direta - Reddit bloqueia)

### Canva
- Client ID: `***REDACTED***`
- Client Secret: `***REDACTED***`
- Access Token: Configurado em `canva_automation/.canva_tokens.json`
- Scripts: `canva_automation/` (automação independente)

### OpenAI
- **NÃO CONFIGURADO** (precisa criar API key em https://platform.openai.com/api-keys)

---

## Scripts Funcionais

### PowerShell (UTF-8 Encoding)

**IMPORTANT:** Usar PowerShell 5.1 requer `-Encoding UTF8` e `[System.Text.Encoding]::UTF8.GetBytes()` para evitar corrupção de caracteres especiais.

| Script | Canal | Como usar |
|---|---|---|
| `devto_post_utf8.ps1` | Dev.to | `powershell -ExecutionPolicy Bypass -File "devto_post_utf8.ps1" "output/arquivo.json"` |
| `linkedin_post_utf8.ps1` | LinkedIn | `powershell -ExecutionPolicy Bypass -File "linkedin_post_utf8.ps1" "output/arquivo.json"` |

### Node.js (Reddit via CDP)

| Script | Canal | Como usar |
|---|---|---|
| `reddit_post.js` | Reddit | Ver instruções abaixo |
| `publish_devto.py` | Dev.to | `python publish_devto.py output/arquivo.json` |
| `publish_linkedin.py` | LinkedIn | `python publish_linkedin.py output/arquivo.json` |

**GitHub Actions (Linux):**
- `publish_devto.py` e `publish_linkedin.py` funcionam no Ubuntu
- Workflow: `.github/workflows/weekly-content.yml`
- Execução manual via `workflow_dispatch`

**Para usar o Reddit:**

1. Executar `start_chrome.bat` para abrir Chrome com debug port
2. Fazer login manual no Reddit no Chrome
3. Executar: `node reddit_post.js "output/arquivo.json" "Subreddit"`

**Para postar em múltiplos subreddits:**
```bash
node reddit_post.js "output/arquivo.json" "SideProject,Python,coolgithubprojects"
```

### Scripts Python (QUEBRADOS - não usar)

⚠️ **Python 3.14 está quebrado neste ambiente** - módulo `tempfile` ausente. Os scripts Python (`social_scheduler.py`, `content_generator.py`, etc.) NÃO funcionam. Use apenas PowerShell e Node.js.

---

## Conteúdo Gerado

Arquivos JSON em `output/`:

| Arquivo | Projetos | Canais |
|---|---|---|
| `2026-08-19_qa_overflow_all_content.json` | QA Overflow | Dev.to + LinkedIn + Reddit |
| `2026-08-19_scandoc_all_content.json` | ScanDoc | Dev.to + LinkedIn + Reddit |
| `2026-08-19_supertarefas_all_content.json` | SuperTarefas | LinkedIn + Reddit |
| `2026-08-19_qa_picker_all_content.json` | QA Picker | Dev.to + LinkedIn + Reddit |

**IMPORTANTE:** Os posts do Reddit precisam ser escritos em INGLÊS para subreddits internacionais. Posts em português são apenas para o Reddit brasileiro.

---

## Posts Publicados (19/08/2026)

| Canal | Projeto | URL |
|---|---|---|
| Dev.to | QA Overflow | https://dev.to/victorholiveira/design-patterns-para-automacao-de-testes-guia-pratico-com-playwright-e-cypress-2dae |
| LinkedIn | ScanDoc | Post ID: 7495823373134983168 |
| Reddit | ScanDoc | https://www.reddit.com/r/SideProject/comments/1vsn0lv/ |
| Reddit | ScanDoc | https://www.reddit.com/r/ChatGPT/comments/1vsmm72/ (removido) |

---

## Subreddits Recomendados

### Regras Importantes
- **Regra 90/10:** No máximo 10% da atividade deve ser autopromoção
- **Sempre declare** que é o criador
- **Warmup:** 2-4 semanas de engajamento antes de postar
- **Melhor horário:** Terça-Quinta, 7-9h (horário de Brasília)

### Por Projeto

**ScanDoc:**
- r/SideProject ✅ (funcionou)
- r/Python
- r/coolgithubprojects
- r/ChatGPT (weekly self-promo thread)
- r/netsec
- r/opensource

**QA Overflow:**
- r/SideProject
- r/indiehackers
- r/webdev (Showoff Saturday)
- r/coolgithubprojects

**QA Picker:**
- r/SideProject
- r/chrome_extensions (melhor encaixe)
- r/coolgithubprojects
- r/webdev (Showoff Saturday)
- r/webscraping (monthly thread)

**SuperTarefas:**
- r/SideProject
- r/FlutterDev
- r/alphaandbetausers
- r/androidapps (weekly self-promo)

### Subreddits que BANEM Autopromoção
- r/QualityAssurance
- r/softwaretesting
- r/programming
- r/InternetIsBeautiful

---

## Estrutura de Diretórios

```
D:\Marketing\automation\
├── config.yaml              # Configuração central
├── config.example.yaml      # Template de configuração
├── .gitignore               # Ignora config.yaml (tem senhas)
├── requirements.txt         # Dependências Python (quebrado)
├── package.json             # Dependências Node.js
├── package-lock.json        # Lock file
├── start_chrome.bat         # Abre Chrome com debug port
├── run.bat                  # Launcher geral (quebrado - depende de Python)
│
├── # Scripts PowerShell (FUNCIONAIS)
├── devto_post_utf8.ps1      # Publica no Dev.to
├── linkedin_post_utf8.ps1   # Publica no LinkedIn
│
├── # Scripts Node.js (FUNCIONAIS)
├── reddit_post.js           # Publica no Reddit via CDP
│
├── # Scripts Python (QUEBRADOS - precisam reinstalação)
├── social_scheduler.py      # Orquestrador principal
├── content_generator.py     # Geração de conteúdo via OpenAI
├── canva_generator.py       # Imagens via Canva API
├── devto_publisher.py       # Dev.to publisher
├── linkedin_publisher.py    # LinkedIn publisher
├── reddit_publisher.py      # Reddit publisher (PRAW)
├── twitter_publisher.py     # Twitter publisher
├── medium_importer.py       # Medium importer
├── seo_monitor.py           # Monitor SEO
├── topic_generator.py       # Gerador de tópicos
│
├── # Scripts OAuth (Histórico)
├── linkedin_oauth.ps1
├── linkedin_oauth2.ps1
├── linkedin_oauth_final.ps1 # Script que funcionou para LinkedIn
├── linkedin_oauth.py        # Script Python (quebrado)
│
├── output/                  # Conteúdo gerado e tokens
│   ├── linkedin_token.json  # Token LinkedIn
│   ├── *.json               # Conteúdo para publicação
│   └── *.png                # Screenshots de debug
│
├── .github/workflows/       # GitHub Actions
│   └── weekly-content.yml   # Pipeline semanal
│
└── node_modules/            # Puppeteer-core
```

---

## Configuração Inicial na Nova VM

### 1. Pré-requisitos
- **Node.js** v18+ (funcionou v25.6.1)
- **Google Chrome** instalado
- **PowerShell** 5.1+ (Windows)
- **Python** (opcional - está quebrado, mas pode reinstalar)

### 2. Setup do Projeto
```bash
# Copiar toda a pasta D:\Marketing\automation para a nova VM
# Entrar na pasta
cd D:\Marketing\automation

# Instalar dependências Node.js
npm install

# Verificar se Chrome está instalado
dir "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### 3. Configurar Credenciais
Copiar o `config.yaml` (com credenciais) para a nova VM. **NUNCA commite no Git.**

### 4. Primeiro Login
```bash
# Iniciar Chrome com debug port
start start_chrome.bat

# Fazer login manual no Reddit no Chrome

# Testar Dev.to
powershell -ExecutionPolicy Bypass -File "devto_post_utf8.ps1" "output/2026-08-19_qa_overflow_all_content.json"

# Testar LinkedIn
powershell -ExecutionPolicy Bypass -File "linkedin_post_utf8.ps1" "output/2026-08-19_scandoc_all_content.json"

# Testar Reddit
node reddit_post.js "output/2026-08-19_scandoc_all_content.json" "SideProject"
```

---

## O Que Precisa Ser Feito (Prioridade)

### Alta Prioridade
1. **OpenAI API Key** - Criar em https://platform.openai.com/api-keys (~$5)
   - Modelo recomendado: `gpt-4o-mini` ($0.15/1M tokens)
   - Usar para gerar conteúdo automaticamente
   - Atualizar `config.yaml` com a key

2. **Reddit Warmup** - Conta scandoc_dev precisa de 2-4 semanas de engajamento genuíno
   - Comentar em posts existentes
   - Upvotar conteúdo relevante
   - Evitar autopromoção direta

### Média Prioridade
3. **Canva OAuth** ✅ - Configurado em 19/08/2026
   - Scripts em `canva_automation/`
   - Tokens em `.canva_tokens.json`

4. **GitHub Actions** ✅ - Configurado em 19/08/2026
   - Workflow: `.github/workflows/weekly-content.yml`
   - Scripts Linux: `publish_devto.py`, `publish_linkedin.py`
   - Execução manual via `workflow_dispatch`

5. **Reinstalar Python** (opcional)
   - Desinstalar Python 3.14 atual
   - Instalar Python 3.12 (mais estável)
   - Executar: `pip install -r requirements.txt`

### Baixa Prioridade
6. **Twitter/X** - Configurar se quiser
   - Criar app em https://developer.x.com/
   - Custo: $0.015/texto, $0.20/link

7. **Medium** - Importação manual por enquanto
   - Copiar artigo do Dev.to
   - Colar no Medium com canonical URL

8. **Automação Completa** - Configurar `social_scheduler.py`
   - Depende de Python funcionando
   - Depende de OpenAI configurado

---

## Comandos Úteis

```bash
# Verificar se Chrome está rodando na porta 9222
Get-NetTCPConnection -LocalPort 9222

# Fechar Chrome
taskkill /F /IM chrome.exe

# Listar artigos no Dev.to
$headers = @{"api-key" = "ZPSxjy5NUavCnYVGKva39uMU"}
Invoke-WebRequest -Uri "https://dev.to/api/articles/me/published" -Headers $headers

# Despublicar artigo no Dev.to
$body = '{"article": {"published": false}}'
$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
Invoke-WebRequest -Uri "https://dev.to/api/articles/ID" -Method Patch -Body $bytes -Headers $headers

# Verificar posts recentes do Reddit
node -e "const p = require('puppeteer-core'); (async()=>{const b = await p.connect({browserURL:'http://127.0.0.1:9222'}); const pg = await b.newPage(); await pg.goto('https://www.reddit.com/user/scandoc_dev/posts/'); await new Promise(r=>setTimeout(r,3000)); console.log(await pg.evaluate(()=>document.body.innerText.substring(0,1000))); b.disconnect();})()"
```

---

## Notas Importantes

1. **Encoding UTF-8 é CRÍTICO** - PowerShell 5.1 lê arquivos como cp1252 por padrão. Sempre usar `-Encoding UTF8` e `[System.Text.Encoding]::UTF8.GetBytes()`.

2. **Reddit via API direta NÃO funciona** - O Reddit bloqueia autenticação de apps novos. A única forma que funciona é via automação de browser (Puppeteer CDP).

3. **Chrome precisa estar aberto** - Para publicar no Reddit, execute `start_chrome.bat` primeiro e faça login manual.

4. **Contas novas são fiscalizadas** - Reddit remove contas com menos de 30 dias que postam links/comercial. Construa karma primeiro.

5. **Dry Run** - O `config.yaml` tem `dry_run: true` por padrão. Mude para `false` quando pronto para publicar em massa.

---

*Última atualização: 19/08/2026*
*Criado por: Victor Oliveira*
