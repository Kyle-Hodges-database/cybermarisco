from dotenv import load_dotenv
from io import BytesIO
from os import getenv
import argparse
import logging
import asyncio
import random
from seleniumbase import cdp_driver
from playwright.async_api import async_playwright, expect, Page, BrowserContext, TimeoutError
from PIL import Image
from PruebaDeteccion import img_to_action, TooManyButtonsException
from text import img_to_apuesta

BASE_URL = "https://www.betsson.es"

logger = logging.getLogger("betsson")

def get_creds(money: bool) -> tuple:
    logger.info(f"Fetching creds for user with money={money}")
    if money:
        return (getenv('ACCOUNT_MONEY_EMAIL'), getenv('ACCOUNT_MONEY_PASSWORD'))
    return (getenv('ACCOUNT_BROKE_EMAIL'), getenv('ACCOUNT_BROKE_PASSWORD'))

async def close_cookies(page: Page):
    accept_cookies_btn = page.locator("#onetrust-accept-btn-handler")
    try:
        await accept_cookies_btn.wait_for(state="visible", timeout=10000)
        logger.info("Closing cookie banner")
        await accept_cookies_btn.click()
    except TimeoutError:
        pass

async def do_login(page: Page, creds: tuple):
    logger.info("Attempting login")
    login_btn = page.get_by_test_id("btn-1").get_by_role("button", name="Iniciar sesión")
    await expect(login_btn).to_have_count(1)
    await login_btn.click()

    email_input = page.get_by_test_id("email-input")
    await email_input.fill(creds[0])

    password_input = page.get_by_test_id("password-input")
    await password_input.fill(creds[1])

    submit_btn = page.get_by_test_id("account-login-btn-1-button")
    await submit_btn.click()

    auth_btn = page.get_by_test_id("dialog-close-button")
    has_auth = await auth_btn.count() == 1
    if has_auth:
        logger.info("Closing 'use key' dialog")
        await auth_btn.click()

    
    consent_btn = page.get_by_test_id("logiimage_stream = io.BytesIO(image_bytes)n-consent-cta-btn-1")
    has_consent = await consent_btn.count() == 1
    if has_consent:
        logger.info(f"Closing consent dialog")
        await consent_btn.click()

async def capture_balance(page: Page) -> float:
    logger.info(f"Trying to fetch initial balance")
    async with page.expect_response("**/api/v2/wallet/balance*") as response_info:
        response = await response_info.value
        data = await response.json()
        return data['balance']['totalAmount']

async def get_game(page: Page) -> tuple:
    slider = page.get_by_test_id("preview-section-HomepageCasino.quick-links")
    anchors = await slider.locator("a.preview-item").all()

    anchor = random.choice(anchors)

    return (await anchor.inner_text(), await anchor.get_attribute("href"))

async def handle_safety(page: Page, initialBalance: float):
    blocked = page.locator("gaming-game_dgoj_session_blocked")
    try:
        await blocked.wait_for(state="visible", timeout=10000)
        logger.info("Handling anti-addiction mecanisims")
        # Caso: Vuelves a jugar después de terminar tu sesión en poco tiempo
        adict_btn = page.get_by_test_id("start-new-session-buttons-btn-2-button")
        await adict_btn.wait_for(state="visible", timeout=10000)
        await adict_btn.click()
        await set_session_timer(page)
    except TimeoutError:
        pass

async def set_session_timer(page: Page):
    await page.get_by_test_id("session-settings_time-limit-option-18000").click()
    await page.get_by_test_id("session-settings_spending-limit-option-100").click()
    await page.get_by_test_id("session-settings_submit-button-btn-1-button").click()

async def play_game(page: Page, game: tuple, initialBalance: float):
    gameFiltered = game[0].replace("\n", " ")
    logger.info(f"Playing {gameFiltered}")
    await page.goto(BASE_URL + game[1], wait_until="domcontentloaded")

    await close_cookies(page)

    await handle_safety(page, initialBalance)

    frame = page.locator(".iframe-container")

    i = 0
    badButtonsTimes = 0
    currentBalance = initialBalance
    while i < 20 and badButtonsTimes < 5:
        frame_bytes = await frame.screenshot(type="png")
        image_stream = BytesIO(frame_bytes)
        img = Image.open(image_stream)

        apuesta = img_to_apuesta(img)
        if apuesta is not None:
            logger.info(f"Detected bet amount: {apuesta}")
        else:
            logger.warning("No bet amount detected")

        try:
            action = img_to_action(img)
            logger.info(action)
            if action is not None:
                logger.info(f"Action detected: {action}")
                await frame.click(position={"x": action[0], "y": action[1]})
            else:
                logger.warning("No action coords detected")
        except TooManyButtonsException:
            logger.warning("Too many possible buttons, skipping")
            badButtonsTimes += 1

        await asyncio.sleep(5.0)

        i += 1

async def main():
    logging.basicConfig(filename='out.log', level=logging.INFO)
    load_dotenv()

    parser = argparse.ArgumentParser(
                    prog='GameTester',
                    description='Game checker for Betsson ',
                    epilog='Made with <3 (and energy drinks) by CyberMariscos')
    
    parser.add_argument('--headless', help="Run in headless mode", action='store_true', default=False)
    parser.add_argument('-m', '--money', help="Use account with money", action='store_true', default=True)

    args = parser.parse_args()

    creds = get_creds(money=args.money)
    driver = await cdp_driver.start_async(headless=args.headless)

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
                logger.info(f"Total initial balance: {balance}")

                game = await get_game(page)

                await play_game(page, game, balance)
            finally:
                await browser.close()
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
