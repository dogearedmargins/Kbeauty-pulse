export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { region, context, type } = req.body;

  const prompts = {
    trend: `K-Beauty B2B 마케팅 전문가로서 아래 데이터 기반으로 3문장 인사이트를 한국어로 작성하세요.\n${context}`,
    keyword: `K-Beauty 키워드 애널리스트로서 아래 트렌딩 키워드 분석해 마케팅 전략 3문장 한국어로.\n지역:${region}\n${context}`
  };

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.GROQ_API_KEY}`
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          { role: 'user', content: prompts[type] || prompts.trend }
        ],
        max_tokens: 600,
        temperature: 0.7
      })
    });

    const data = await response.json();
    const text = data?.choices?.[0]?.message?.content;
if (!text) {
  console.error('Groq response:', JSON.stringify(data));
  return res.status(200).json({ result: '분석 실패: ' + JSON.stringify(data) });
}
    
    res.status(200).json({ result: text });
  } catch (error) {
    res.status(500).json({ error: '분석 중 오류가 발생했습니다.' });
  }
}
