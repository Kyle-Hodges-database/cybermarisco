from dotenv import load_dotenv
from os import getenv
import asyncio
from playwright.async_api import async_playwright, expect, Page

def get_creds(money: bool) -> tuple:
    if money:
        return (getenv('ACCOUNT_MONEY_EMAIL'), getenv('ACCOUNT_MONEY_PASSWORD'))

    return (getenv('ACCOUNT_BROKE_EMAIL'), getenv('ACCOUNT_BROKE_PASSWORD'))

async def do_login(page: Page, creds: tuple):
    login_btn = page.get_by_test_id("btn-1").get_by_role("button", name="Iniciar sesión")
    await expect(login_btn).to_have_count(1)
    await login_btn.click()

    email_input = page.get_by_test_id("email-input")
    await email_input.fill(creds[0])

    password_input = page.get_by_test_id("password-input")
    await password_input.fill(creds[1])

    submit_btn = page.get_by_test_id("account-login-btn-1-button")
    await submit_btn.click()

async def main():
    load_dotenv()
    creds = get_creds(money=True)

    fetch_patch = ''
    with open('scripts/fetch.js') as f:
        fetch_patch = f.read()

    async with async_playwright() as p:
        p.selectors.set_test_id_attribute("data-test-id")

        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        await page.add_init_script(fetch_patch)

        await page.goto("https://www.betsson.es", wait_until="domcontentloaded")

        # Hacer login
        await do_login(page, creds)

        await asyncio.sleep(1000)
        await browser.close()

asyncio.run(main())
