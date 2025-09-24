import asyncio
from playwright.async_api import async_playwright, expect
import random
import string

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Generate random user credentials
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"user_{random_string}@example.com"
        password = "password123"

        # 1. Sign up a new user
        await page.goto("http://localhost:5173/signup")
        await page.get_by_label("Email").fill(email)
        await page.get_by_label("Password").fill(password)
        await page.get_by_label("Confirm Password").fill(password)
        await page.get_by_role("button", name="Sign Up").click()

        # Wait for navigation to the login page after successful signup
        await expect(page).to_have_url("http://localhost:5173/login")
        print("Successfully signed up.")

        # 2. Log in
        await page.get_by_label("Email").fill(email)
        await page.get_by_label("Password").fill(password)
        await page.get_by_role("button", name="Login").click()

        # Wait for navigation to the tenants page
        await expect(page).to_have_url("http://localhost:5173/tenants")
        print("Successfully logged in.")

        # 3. Create a new tenant
        await page.get_by_role("button", name="Create New Tenant").click()

        # Modal appears, fill in the form
        await expect(page.get_by_role("heading", name="Create New Tenant")).to_be_visible()
        await page.get_by_label("Tenant Name").fill("Test Tenant")

        # Verify the dropdowns in the modal
        doc_lang_modal = page.locator("#doc_language")
        trans_target_modal = page.locator("#translation_target")

        await expect(doc_lang_modal).to_have_value("en")
        await expect(trans_target_modal).to_have_value("en")

        await doc_lang_modal.select_option("de")
        await trans_target_modal.select_option("fr")

        await expect(doc_lang_modal).to_have_value("de")
        await expect(trans_target_modal).to_have_value("fr")

        await page.screenshot(path="jules-scratch/verification/create_tenant_modal.png")
        print("Took screenshot of create tenant modal.")

        await page.get_by_role("button", name="Create").click()

        # Wait for the new tenant to appear
        await expect(page.get_by_role("heading", name="Test Tenant")).to_be_visible()
        print("Successfully created tenant.")

        # 4. Navigate to tenant settings
        await page.get_by_role("link", name="Test Tenant").click()
        await page.get_by_role("tab", name="Settings").click()

        await expect(page.get_by_role("heading", name="Settings")).to_be_visible()
        print("Navigated to settings page.")

        # 5. Verify the dropdowns and take a screenshot
        doc_lang_settings = page.locator("#doc_language")
        trans_target_settings = page.locator("#translation_target")

        # The values should persist from creation
        await expect(doc_lang_settings).to_have_value("de")
        await expect(trans_target_settings).to_have_value("fr")

        # Change the values
        await doc_lang_settings.select_option("en")
        await trans_target_settings.select_option("en")

        await expect(doc_lang_settings).to_have_value("en")
        await expect(trans_target_settings).to_have_value("en")

        await page.screenshot(path="jules-scratch/verification/settings_page.png")
        print("Took screenshot of settings page.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
