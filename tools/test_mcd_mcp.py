import asyncio
import httpx
from mcp.client.sse import sse_client
from mcp import ClientSession

async def test_mcd():
    url = "https://mcp.mcd.cn/sse"
    headers = {
        "Authorization": "Bearer 2hez4lKA1OCBpMnFf7YaP8qVg5aR0ubY"
    }
    
    print(f"Testing connection to {url}...")
    try:
        async with sse_client(url=url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print(f"Success! Found {len(tools.tools)} tools")
    except Exception as e:
        print(f"Failed with error: {e}")
        # 探测是否有子路径
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            print(f"GET root status: {resp.status_code}")
            print(f"GET root body: {resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_mcd())
