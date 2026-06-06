const RSS_SOURCES = [
  { name: 'WWD', url: 'https://wwd.com/feed/', lang: 'en' },
  { name: 'BeautyMatter', url: 'https://beautymatter.com/feed/', lang: 'en' },
  { name: 'CosmeticsDesign-Asia', url: 'https://www.cosmeticsdesign-asia.com/rss/news', lang: 'en' },
  { name: 'CosmeticsBusiness', url: 'https://cosmeticsbusiness.com/rss', lang: 'en' },
  { name: 'KOTRA', url: 'https://dream.kotra.or.kr/kotranews/rss/rssAll.do', lang: 'ko' },
  { name: '조선비즈', url: 'https://biz.chosun.com/arc/outboundfeeds/rss/category/distribution/', lang: 'ko' },
];

const KBEAUTY_KEYWORDS = [
  'k-beauty', 'k beauty', 'korean beauty', 'korean skincare', 'k뷰티', '케이뷰티',
  'korean cosmetics', '화장품 수출', 'k-cosmetics', 'medicube', 'beauty of joseon',
  'cosrx', 'olive young', 'amorepacific', 'lg생활건강'
];

async function fetchRSS(source) {
  try {
    const res = await fetch(source.url, {
      headers: { 'User-Agent': 'KBeautyPulse/1.0' },
      signal: AbortSignal.timeout(5000)
    });
    const text = await res.text();
    const items = [];
    const itemRegex = /<item>([\s\S]*?)<\/item>/gi;
    let match;
    while ((match = itemRegex.exec(text)) !== null) {
      const item = match[1];
      const title = (item.match(/<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?<\/title>/i) || [])[1]?.trim() || '';
      const link = (item.match(/<link[^>]*>(.*?)<\/link>/i) || [])[1]?.trim() || '';
      const pubDate = (item.match(/<pubDate>(.*?)<\/pubDate>/i) || [])[1]?.trim() || '';
      const desc = (item.match(/<description[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>/i) || [])[1]?.trim().replace(/<[^>]+>/g, '').substring(0, 200) || '';
      
      if (title && link) {
        items.push({ title, link, pubDate, desc, source: source.name });
      }
    }
    return items.slice(0, 20);
  } catch (e) {
    return [];
  }
}

function isKBeautyRelevant(item) {
  const text = (item.title + ' ' + item.desc).toLowerCase();
  return KBEAUTY_KEYWORDS.some(kw => text.includes(kw.toLowerCase()));
}

async function selectWithGroq(articles, region) {
  const articleList = articles.slice(0, 15).map((a, i) => 
    `${i+1}. [${a.source}] ${a.title}`
  ).join('\n');

  const prompt = `당신은 K-Beauty B2B 영업 전문가입니다.
아래 기사 목록에서 "${region}" 지역 바이어/마케터에게 가장 유의미한 기사 3개를 선택하세요.

선택 기준:
- 실제 매출/수출 데이터가 포함된 기사 우선
- 신규 채널 론칭, 파트너십, 입점 관련
- 브랜드 IPO, 투자, M&A 관련
- 소비자 트렌드 변화 (정량 데이터 포함)

기사 목록:
${articleList}

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만:
{"selected":[{"index":1,"reason":"선택 이유 한 줄"},{"index":2,"reason":"선택 이유 한 줄"},{"index":3,"reason":"선택 이유 한 줄"}]}`;

  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.GROQ_API_KEY}`
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 300,
        temperature: 0.3
      })
    });
    const data = await res.json();
    const text = data.choices?.[0]?.message?.content || '{}';
    const clean = text.replace(/```json|```/g, '').trim();
    return JSON.parse(clean);
  } catch (e) {
    return { selected: [{ index: 0 }, { index: 1 }, { index: 2 }] };
  }
}

function getImageKeyword(title, source) {
  const lower = title.toLowerCase();
  if (lower.includes('tiktok')) return 'TikTok beauty social media';
  if (lower.includes('spf') || lower.includes('sunscreen') || lower.includes('선크림')) return 'sunscreen beauty SPF';
  if (lower.includes('serum') || lower.includes('세럼')) return 'Korean serum skincare';
  if (lower.includes('pdrn')) return 'clinic skincare treatment';
  if (lower.includes('amazon')) return 'online beauty shopping';
  if (lower.includes('sephora')) return 'Sephora beauty store';
  if (lower.includes('ipo') || lower.includes('투자')) return 'business finance growth';
  if (lower.includes('수출') || lower.includes('export')) return 'Korean beauty export global';
  return 'Korean beauty skincare luxury';
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const region = req.query.region || 'Americas';

  try {
    // 1. RSS 수집
    const allArticles = [];
    const fetchPromises = RSS_SOURCES.map(source => fetchRSS(source));
    const results = await Promise.allSettled(fetchPromises);
    
    results.forEach(result => {
      if (result.status === 'fulfilled') {
        allArticles.push(...result.value);
      }
    });

    // 2. K-beauty 관련 필터링
    const relevant = allArticles.filter(isKBeautyRelevant);
    
    if (relevant.length === 0) {
      return res.status(200).json({ articles: [], message: 'No relevant articles found' });
    }

    // 3. Groq AI로 3개 선별
    const selected = await selectWithGroq(relevant, region);
    
    // 4. 선별된 기사 반환
    const cards = (selected.selected || []).slice(0, 3).map((sel, i) => {
      const article = relevant[sel.index] || relevant[i] || relevant[0];
      const types = ["THIS WEEK'S LEAD", "NUMBERS", "ON THE RADAR"];
      const bgs = ['unsplash', 'gradient', 'unsplash'];
      return {
        type: types[i],
        title: article.title,
        source: article.source,
        date: article.pubDate ? new Date(article.pubDate).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) : '',
        url: article.link,
        image_keyword: getImageKeyword(article.title, article.source),
        bg: bgs[i],
        number: i === 1 ? '' : undefined,
        number_label: i === 1 ? sel.reason || '' : undefined,
        reason: sel.reason || ''
      };
    });

    res.status(200).json({ articles: cards, total_found: relevant.length });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
