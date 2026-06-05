import os
import json
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "generated papers")

async def save_pdf_background(html_content: str, raw_json_str: str, subject: str, level: str, title: str):
    """
    Background task to generate a PDF from HTML and save the raw JSON data.
    Uses Playwright headless Chromium.
    """
    try:
        # Ensure directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Clean filename
        safe_title = "".join([c if c.isalnum() or c in [" ", "_", "-"] else "_" for c in title]).strip()
        safe_title = safe_title.replace(" ", "_").lower()
        
        pdf_path = os.path.join(OUTPUT_DIR, f"{safe_title}.pdf")
        json_path = os.path.join(OUTPUT_DIR, f"{safe_title}.json")
        
        # Save JSON data immediately
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(raw_json_str)
            
        print(f"[PDF Engine] Starting background PDF generation for: {safe_title}")
        
        # Convert relative image URLs to absolute localhost URLs so Playwright can fetch them
        html_content = html_content.replace('src="/api/', 'src="http://localhost:8000/api/')
        html_content = html_content.replace('src="/static/', 'src="http://localhost:8000/static/')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()
            
            # Inject the HTML
            await page.set_content(html_content, wait_until="networkidle")
            
            # Generate the PDF
            await page.pdf(
                path=pdf_path,
                format="A4",
                print_background=True,
                display_header_footer=False,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
            )
            
            await browser.close()
            
        print(f"[PDF Engine SUCCESS] Successfully saved PDF and JSON to /generated papers: {safe_title}")
    except Exception as e:
        print(f"[PDF Engine ERROR] Failed to generate PDF: {str(e).encode('ascii', errors='ignore').decode('ascii')}")
