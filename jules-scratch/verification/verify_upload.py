import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Sign up a new user
            await page.goto("http://localhost:4173/signup")
            await page.get_by_label("Email").fill("test@example.com")
            await page.get_by_label("Password").fill("password123")
            await page.get_by_role("button", name="Sign Up").click()
            await page.wait_for_url("**/manage-tenants")
            print("Sign up successful")

            # Log out to test login
            await page.get_by_role("button", name="Profile").click()
            await page.get_by_role("button", name="Log Out").click()
            await page.wait_for_url("**/login")
            print("Log out successful")

            # Log in
            await page.goto("http://localhost:5173/login")
            await page.get_by_label("Email").fill("test@example.com")
            await page.get_by_label("Password").fill("password123")
            await page.get_by_role("button", name="Login").click()
            await page.wait_for_url("**/manage-tenants")
            print("Login successful")

            # Create a new tenant
            await page.get_by_role("button", name="Create New Assistant").click()
            await page.get_by_label("Assistant Name").fill("Test Assistant")
            await page.get_by_label("Intro Message").fill("Hello!")
            await page.get_by_label("System Persona").fill("You are a helpful assistant.")
            await page.get_by_label("Prompt Template").fill("Answer the question: {question}")
            await page.get_by_role("button", name="Create Assistant").click()
            await page.wait_for_selector("text=Test Assistant")
            print("Tenant creation successful")

            # Navigate to the new tenant's page
            await page.get_by_role("link", name="Test Assistant").click()

            # Go to sources tab
            await page.get_by_role("link", name="Sources").click()
            await page.wait_for_url("**/sources")
            print("Navigated to sources page")

            # Upload file
            file_path = "jules-scratch/verification/events.csv"
            await page.locator('input[type="file"]').set_input_files(file_path)
            await page.get_by_role("button", name="Upload File").click()

            # Wait for the toast message and take a screenshot
            toast = page.locator(".toast")
            await expect(toast).to_be_visible()
            await page.screenshot(path="jules-scratch/verification/upload_toast.png")
            print("Screenshot taken")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="jules-scratch/verification/error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
