
import asyncio
from main import app
from httpx import AsyncClient, ASGITransport

async def run():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        for i in range(5):
            await client.post('/books/', json={'title': f'Book {i}', 'author': 'Author', 'year': 2000+i})
        resp1 = await client.get('/books/?limit=2&sort_by=year')
        print('Page 1:', resp1.json()['items'])
        print('next_url:', resp1.json()['next_url'])
        resp2 = await client.get(resp1.json()['next_url'])
        print('Page 2:', resp2.json()['items'])

asyncio.run(run())
