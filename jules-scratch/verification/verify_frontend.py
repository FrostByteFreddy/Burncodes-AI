import time
import os
from playwright.sync_api import sync_playwright, expect
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from backend .env
load_dotenv(dotenv_path='../backend/.env')

def run_verification(playwright):
    # --- Supabase Admin Setup ---
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not service_key:
        raise EnvironmentError("Supabase credentials not found in backend/.env")

    supabase_admin: Client = create_client(url, service_key)

    # --- Test User Creation ---
    unique_email = f"testuser_{int(time.time())}@example.com"
    password = "password123"
    try:
        supabase_admin.auth.admin.create_user({
            "email": unique_email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"first_name": "Test", "last_name": "User"}
        })
        print(f"✅ Successfully created test user: {unique_email}")
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return

    # --- Playwright Test ---
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Navigate to the login page
        page.goto("http://localhost:5173/login")

        # Fill out the login form
        page.get_by_label("Email").fill(unique_email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()

        # Verify navigation to the dashboard
        expect(page).to_have_url("http://localhost:5173/dashboard", timeout=10000)

        # Verify the dashboard heading is visible
        dashboard_heading = page.get_by_role("heading", name="My Tenants")
        expect(dashboard_heading).to_be_visible()

        # Wait for the loading message to disappear
        expect(page.get_by_text("Loading tenants...")).to_be_hidden(timeout=10000)

        # Check for either the success message or an error message
        no_tenants_locator = page.get_by_text("No tenants found")
        error_locator = page.get_by_text("Error:")

        expect(no_tenants_locator.or_(error_locator)).to_be_visible()

        # Take a screenshot of the dashboard
        page.screenshot(path="jules-scratch/verification/dashboard_after_fix.png")

        # Assert that there is no error
        expect(error_locator).to_be_hidden()
        print("✅ Verification successful, screenshot taken.")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        page.screenshot(path="jules-scratch/verification/failure_after_fix.png")
    finally:
        browser.close()
        # Clean up the created user
        try:
            users_list = supabase_admin.auth.admin.list_users()
            user_to_delete = next((u for u in users_list if u.email == unique_email), None)
            if user_to_delete:
                supabase_admin.auth.admin.delete_user(user_to_delete.id)
                print(f"✅ Cleaned up test user: {unique_email}")
        except Exception as e:
            print(f"⚠️ Failed to clean up test user: {e}")

    # Add a delay before the final assertions
    page.wait_for_timeout(2000)


with sync_playwright() as playwright:
    run_verification(playwright)
