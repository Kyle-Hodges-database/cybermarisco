import asyncio
from playwright.async_api import async_playwright, expect, Page

async def do_login(page: Page):
    login_btn = page.get_by_test_id("btn-1").get_by_role("button", name="Iniciar sesión")
    await expect(login_btn).to_have_count(1)
    await login_btn.click()

    email_input = page.get_by_test_id("email-input")
    await email_input.fill("edyth2026101598184900pdiwfxhad@betssongroup.com")

    password_input = page.get_by_test_id("password-input")
    await password_input.fill("SmokeTest123")

    submit_btn = page.get_by_test_id("account-login-btn-1-button")
    await submit_btn.click()

async def main():
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
        await do_login(page)

        await asyncio.sleep(1000)
        await browser.close()

asyncio.run(main())
