from dotenv import load_dotenv
from os import getenv
import asyncio
import browser_cookie3
import random
from playwright.async_api import async_playwright, expect, Page, BrowserContext

DOMAIN = "betsson.es"
BASE_URL = "https://www.betsson.es"

def get_chrome_cookies(domain: str) -> list[dict]:
    print("Getting cookies")
    cookies = []
    cj = browser_cookie3.chromium(domain_name=domain)
    
    for c in cj:
        cookies.append({
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path,
            "expires": c.expires if c.expires else -1,
            "httpOnly": bool(c._rest.get("HttpOnly", False)),
            "secure": bool(c.secure),
            "sameSite": "Lax"
        })
    return cookies

def get_creds(money: bool) -> tuple:
    print("Getting creds")
    if money:
        return (getenv('ACCOUNT_MONEY_EMAIL'), getenv('ACCOUNT_MONEY_PASSWORD'))
    return (getenv('ACCOUNT_BROKE_EMAIL'), getenv('ACCOUNT_BROKE_PASSWORD'))

async def load_fetch_patch(page: Page):
    print("Injecting fetch patch")
    with open('scripts/fetch.js', 'r', encoding='utf-8') as f:
        script = f.read()
        await page.add_init_script(script)

async def do_login(page: Page, creds: tuple):
    print("Doing login")
    login_btn = page.get_by_test_id("btn-1").get_by_role("button", name="Iniciar sesión")
    await expect(login_btn).to_have_count(1)
    await login_btn.click()

    email_input = page.get_by_test_id("email-input")
    await email_input.fill(creds[0])

    password_input = page.get_by_test_id("password-input")
    await password_input.fill(creds[1])

    submit_btn = page.get_by_test_id("account-login-btn-1-button")
    await submit_btn.click()

async def capture_balance(page: Page) -> float:
    print("Getting balance")
    async with page.expect_response("**/api/v2/wallet/balance*") as response_info:
        response = await response_info.value
        data = await response.json()
        return data['balance']['totalAmount']

async def get_game(page: Page) -> tuple:
    slider = page.get_by_test_id("preview-section-HomepageCasino.quick-links")
    anchors = await slider.locator("a").all()

    anchor = random.choice(anchors)

    return (await anchor.inner_text(), await anchor.get_attribute("href"))

async def handle_safety(page: Page):
    is_dialog_visible = await page.get_by_test_id("fds-dialog").is_visible()

    if is_dialog_visible:
        print("Dialog exists and is visible")

async def main():
    load_dotenv()
    creds = get_creds(money=True)

    async with async_playwright() as p:
        p.selectors.set_test_id_attribute("data-test-id")

        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./session",
            headless=False
        )

        cookies = get_chrome_cookies(DOMAIN)
        await browser.add_cookies(cookies)

        page = await browser.new_page()
        await page.goto(BASE_URL, wait_until="domcontentloaded")

        balance = await capture_balance(page)
        print(f"Total initial balance: {balance}")

        game = await get_game(page)

        print(f"Playing {game[0]}")
        await page.goto(BASE_URL + game[1])

        await handle_safety(page)

        await asyncio.sleep(100)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
