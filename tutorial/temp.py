from playwright.sync_api import sync_playwright
import os

# -------------------------
# URLs
# -------------------------
urls = [
    "https://carousel-mvp.streamlit.app",
    "https://carousel-mvp.streamlit.app/Interaction",
    "https://carousel-mvp.streamlit.app/Analytics",
]

# -------------------------
# Output folder
# -------------------------
output_dir = "img/product"
os.makedirs(output_dir, exist_ok=True)

# -------------------------
# Screenshot loop
# -------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for i, url in enumerate(urls, start=1):
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        page.goto(url, wait_until="networkidle")

        # wait for Streamlit render
        page.wait_for_timeout(4000)

        # optional: ensure main content loaded (more robust)
        try:
            page.wait_for_selector("section.main", timeout=5000)
        except:
            pass

        file_path = os.path.join(output_dir, f"page{i}.png")

        page.screenshot(path=file_path, full_page=True)
        print(f"Saved: {file_path}")

        page.close()

    browser.close()
