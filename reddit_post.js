const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  chromePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  debugPort: 9222,
  userDataDir: path.join(process.env.USERPROFILE, '.reddit-automation-profile'),
  humanDelay: { min: 30, max: 120 },
  pageDelay: { min: 2000, max: 5000 },
};

const FLAIR_MAP = {
  'ChatGPT': 'b4536a20-7be9-11ed-9a10-deed22fd00f8',
  'SideProject': null,
  'chrome_extensions': null,
  'FlutterDev': null,
  'indiehackers': null,
  'coolgithubprojects': null,
  'webdev': null,
  'javascript': null,
  'Python': null,
  'androidapps': null,
  'opensource': null,
  'netsec': null,
  'QualityAssurance': null,
  'softwaretesting': null,
};

const SUBREDDIT_DESCRIPTIONS = {
  'SideProject': 'Compartilhar projetos pessoais',
  'chrome_extensions': 'Extensao Chrome',
  'FlutterDev': 'App Flutter',
  'indiehackers': 'Build in public',
  'coolgithubprojects': 'Projeto GitHub',
  'ChatGPT': 'Ferramenta com IA',
  'webdev': 'Desenvolvimento web',
  'Python': 'Projeto Python',
  'androidapps': 'App Android',
  'opensource': 'Codigo aberto',
};

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function randomDelay(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

async function launchChromeWithDebug() {
  const { exec } = require('child_process');
  const chromeArgs = [
    `--remote-debugging-port=${CONFIG.debugPort}`,
    `--user-data-dir=${CONFIG.userDataDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-sync',
    '--translate',
    '--disable-extensions',
    '--disable-infobars',
  ];

  console.log('Iniciando Chrome com debug remoto...');
  exec(`"${CONFIG.chromePath}" ${chromeArgs.join(' ')}`);

  console.log('Aguardando Chrome inicializar...');
  await sleep(5000);
}

async function connectToChrome() {
  try {
    const browser = await puppeteer.connect({
      browserURL: `http://127.0.0.1:${CONFIG.debugPort}`,
      defaultViewport: null,
    });
    console.log('Conectado ao Chrome!');
    return browser;
  } catch (err) {
    console.log('Chrome nao encontrado, iniciando...');
    await launchChromeWithDebug();
    const browser = await puppeteer.connect({
      browserURL: `http://127.0.0.1:${CONFIG.debugPort}`,
      defaultViewport: null,
    });
    console.log('Conectado ao Chrome!');
    return browser;
  }
}

async function loginReddit(page) {
  console.log('Verificando login no Reddit...');
  await page.goto('https://www.reddit.com', { waitUntil: 'networkidle2' });
  await sleep(randomDelay(CONFIG.pageDelay.min, CONFIG.pageDelay.max));

  const url = page.url();
  const hasLogin = url.includes('login') || url.includes('auth');
  
  if (hasLogin) {
    console.log('Nao esta logado. Faca login manualmente no Chrome.');
    console.log('Pressione ENTER quando estiver logado...');
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
  } else {
    console.log('Ja logado no Reddit!');
  }

  return true;
}

async function fetchFlairs(page, subreddit) {
  console.log(`Buscando flairs de r/${subreddit}...`);
  const flairs = await page.evaluate(async (sub) => {
    try {
      const resp = await fetch(`https://www.reddit.com/r/${sub}/api/link_flair.json`, {
        credentials: 'include'
      });
      return await resp.json();
    } catch (e) {
      return [];
    }
  }, subreddit);

  if (Array.isArray(flairs) && flairs.length > 0) {
    console.log('Flairs disponiveis:');
    flairs.forEach(f => {
      const text = f.text || f.richtext?.map(r => r.t).join('') || '';
      console.log(`  ${f.id} | ${text}`);
    });
  }
  return flairs;
}

async function postToReddit(page, subreddit, title, body, flairId) {
  console.log(`\nPreparando post em r/${subreddit}...`);
  await sleep(randomDelay(CONFIG.pageDelay.min, CONFIG.pageDelay.max));

  await page.goto(`https://www.reddit.com/r/${subreddit}/submit`, {
    waitUntil: 'networkidle2',
  });
  await sleep(randomDelay(3000, 6000));

  const payload = {
    sr: subreddit,
    title: title,
    text: body,
    kind: 'self',
    api_type: 'json'
  };

  if (flairId) {
    payload.flair_id = flairId;
  }

  const result = await page.evaluate(async (p) => {
    try {
      const response = await fetch('https://www.reddit.com/api/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(p),
        credentials: 'include'
      });
      const data = await response.json();
      return { status: response.status, data };
    } catch (e) {
      return { error: e.message };
    }
  }, payload);

  if (result.error) {
    console.log('Erro:', result.error);
    return false;
  }

  const errors = result.data?.json?.errors;
  if (errors && errors.length > 0) {
    console.log('Erros do Reddit:', JSON.stringify(errors));
    errors.forEach(e => console.log(`  ${e[0]}: ${e[1]}`));
    return false;
  }

  const postUrl = result.data?.json?.data?.url;
  console.log('Post publicado com sucesso!');
  console.log('URL:', postUrl ? `https://www.reddit.com${postUrl}` : 'Verifique seu perfil');
  return true;
}

async function postToAllSubreddits(page, content, subreddits) {
  let successCount = 0;
  let failCount = 0;

  for (const sub of subreddits) {
    const redditPost = content.reddit?.find(p => p.subreddit === sub);

    if (!redditPost) {
      console.log(`\nNenhum post encontrado para r/${sub}, pulando...`);
      continue;
    }

    const flairId = FLAIR_MAP[sub] || null;
    const desc = SUBREDDIT_DESCRIPTIONS[sub] || sub;

    console.log(`\n${'='.repeat(50)}`);
    console.log(`Postando em r/${sub} (${desc})`);
    console.log(`${'='.repeat(50)}`);

    const success = await postToReddit(page, sub, redditPost.title, redditPost.body, flairId);

    if (success) {
      successCount++;
    } else {
      failCount++;
    }

    if (subreddits.indexOf(sub) < subreddits.length - 1) {
      const waitMinutes = randomDelay(15, 30);
      console.log(`\nAguardando ${waitMinutes} minutos antes do proximo post...`);
      await sleep(waitMinutes * 60 * 1000);
    }
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`RESULTADO: ${successCount} sucesso, ${failCount} falha`);
  console.log(`${'='.repeat(50)}`);
}

async function main() {
  const args = process.argv.slice(2);
  const contentFile = args[0] || path.join(__dirname, 'output', '2026-08-19_scandoc_all_content.json');
  const targetSubs = args[1] ? args[1].split(',') : null;

  if (!fs.existsSync(contentFile)) {
    console.error(`Arquivo nao encontrado: ${contentFile}`);
    process.exit(1);
  }

  const content = JSON.parse(fs.readFileSync(contentFile, 'utf8'));
  const projectName = content.project || 'unknown';

  let subreddits;
  if (targetSubs) {
    subreddits = targetSubs;
  } else {
    subreddits = content.reddit?.map(p => p.subreddit) || [];
  }

  if (subreddits.length === 0) {
    console.error('Nenhum subreddit encontrado no arquivo de conteudo');
    process.exit(1);
  }

  console.log('=== Reddit Automation via CDP ===');
  console.log(`Projeto: ${projectName}`);
  console.log(`Subreddits: ${subreddits.join(', ')}`);
  console.log('');

  const browser = await connectToChrome();
  const page = await browser.newPage();

  try {
    await loginReddit(page);

    if (subreddits.length === 1) {
      const sub = subreddits[0];
      const redditPost = content.reddit?.find(p => p.subreddit === sub);
      if (redditPost) {
        const flairId = FLAIR_MAP[sub] || null;
        await postToReddit(page, sub, redditPost.title, redditPost.body, flairId);
      }
    } else {
      await postToAllSubreddits(page, content, subreddits);
    }
  } catch (err) {
    console.error('Erro:', err.message);
  } finally {
    await page.close();
    browser.disconnect();
    console.log('\nDesconectado do Chrome.');
  }
}

main();
