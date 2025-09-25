from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.wait_for_timeout(5000)
        page.goto("http://localhost:5173/login")
        page.fill('input[type="email"]', "test@test.com")
        page.fill('input[type="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_url("http://localhost:5173/manage-tenants")

        page.click('a[href^="/tenant/"]')
        page.wait_for_url("http://localhost:5173/tenant/**/settings")

        page.click('a:has-text("Widget")')

        page.screenshot(path="jules-scratch/verification/widget-config-form.png")

        primary_color_input = page.locator('input#primary_color')
        primary_color_input.set_input_files([])
        primary_color_input.fill('#FF0000')

        page.screenshot(path="jules-scratch/verification/widget-config-form-filled.png")

        page.click('button:has-text("Save Changes")')

        page.wait_for_timeout(1000)

        page.goto("http://localhost:5173/chat/f0e3e3e3-3e3e-3e3e-3e3e-3e3e3e3e3e3e")

        page.screenshot(path="jules-scratch/verification/chat-widget.png")

        browser.close()

run()