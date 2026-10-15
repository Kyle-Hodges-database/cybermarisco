from dotenv import load_dotenv
from os import getenv
import asyncio
import random
from seleniumbase import cdp_driver
from playwright.async_api import async_playwright, expect, Page, BrowserContext

BASE_URL = "https://www.betsson.es"

def get_creds(money: bool) -> tuple:
    print("Getting creds")
    if money:
        return (getenv('ACCOUNT_MONEY_EMAIL'), getenv('ACCOUNT_MONEY_PASSWORD'))
    return (getenv('ACCOUNT_BROKE_EMAIL'), getenv('ACCOUNT_BROKE_PASSWORD'))

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

    driver = await cdp_driver.start_async(headless=False)

    try:
        endpoint_url = driver.get_endpoint_url()

        async with async_playwright() as p:
            p.selectors.set_test_id_attribute("data-test-id")

            try:
                browser = await p.chromium.connect_over_cdp(endpoint_url)

                context = browser.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()

                await page.goto(BASE_URL, wait_until="domcontentloaded")

                await do_login(page, creds)

                balance = await capture_balance(page)
                print(f"Total initial balance: {balance}")

                game = await get_game(page)

                print(f"Playing {game[0]}")
                await page.goto(BASE_URL + game[1])
            finally:
                await browser.close()
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
