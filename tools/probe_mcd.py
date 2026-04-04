import httpx
import asyncio

async def probe():
    url = "https://mcp.mcd.cn"
    headers = {
        "Authorization": "Bearer 2hez4lKA1OCBpMnFf7YaP8qVg5aR0ubY"
    }
    async with httpx.AsyncClient() as client:
        # 测试 GET
        try:
            r = await client.get(url, headers=headers)
            print(f"GET {url}: {r.status_code}")
            print(f"Headers: {r.headers}")
            print(f"Body: {r.text[:100]}")
        except Exception as e:
            print(f"GET failed: {e}")

        # 测试 POST
        try:
            r = await client.post(url, headers=headers, json={"jsonrpc": "2.0", "method": "list_tools", "params": {}, "id": 1})
            print(f"\nPOST {url}: {r.status_code}")
            print(f"Body: {r.text[:100]}")
        except Exception as e:
            print(f"POST failed: {e}")

if __name__ == "__main__":
    asyncio.run(probe())
