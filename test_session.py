import httpx
import urllib.parse

def check_session(encoded_sid):
    sid = urllib.parse.unquote(encoded_sid)
    headers = {
        "Cookie": f"sessionid={sid}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    url = "https://www.instagram.com/accounts/edit/?__a=1&__d=dis"

    try:
        with httpx.Client(follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            print(f"URL: {resp.url}")
            print(f"Status Code: {resp.status_code}")

            if resp.status_code == 200:
                if "login" in str(resp.url).lower():
                    print("RESULT: Session is EXPIRED or INVALID (redirected to login)")
                else:
                    print("RESULT: Session is VALID!")
                    # Try to see if it's JSON
                    try:
                        data = resp.json()
                        print(f"User found: {data.get('form_data', {}).get('username', 'Unknown')}")
                    except:
                        print("Response was not JSON but stayed on page.")
            elif resp.status_code == 429:
                print("RESULT: RATE LIMITED (IP Blocked)")
            elif resp.status_code == 403:
                print("RESULT: FORBIDDEN (IP Blocked or session rejected)")
            else:
                print(f"RESULT: UNKNOWN ERROR ({resp.status_code})")

    except Exception as e:
        print(f"Error test: {e}")

if __name__ == "__main__":
    test_sid = "49535628499%3AHQxICGmtyUIejp%3A11%3AAYjjeCPp7r27iURg4HBsvDYS6LrWFL_c8SP8xMoKTg"
    check_session(test_sid)
