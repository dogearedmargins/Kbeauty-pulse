export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const { keyword } = req.query;
  if (!keyword) return res.status(400).json({ error: 'keyword required' });

  try {
    const response = await fetch(
      `https://api.unsplash.com/photos/random?query=${encodeURIComponent(keyword)}&orientation=landscape&content_filter=high`,
      {
        headers: {
          'Authorization': `Client-ID ${process.env.UNSPLASH_ACCESS_KEY}`
        }
      }
    );
    const data = await response.json();
    if (data.errors) return res.status(400).json({ error: data.errors[0] });

    res.status(200).json({
      url: data.urls?.regular || data.urls?.full,
      thumb: data.urls?.small,
      credit: data.user?.name,
      credit_url: data.user?.links?.html
    });
  } catch (error) {
    res.status(500).json({ error: '이미지 로드 실패' });
  }
}
