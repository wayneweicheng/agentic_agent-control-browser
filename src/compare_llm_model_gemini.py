from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr
from browser_use import Agent, Controller
from browser_use.agent.views import ActionResult
from dotenv import load_dotenv
import os
import asyncio
import json
import csv
import pathlib

load_dotenv()

# Create a controller to add custom functions
controller = Controller()

# Add custom function to save CSV data
@controller.action("Save data to CSV file")
def save_to_csv(data: str, filename: str) -> str:
    """Save the provided data to a CSV file"""
    try:
        # Create Output directory if it doesn't exist
        output_dir = pathlib.Path("Output")
        output_dir.mkdir(exist_ok=True)
        
        # Write to CSV file
        file_path = output_dir / filename
        with open(file_path, 'w', newline='') as f:
            # Just write the data directly as it's already in CSV format
            f.write(data)
        
        return ActionResult(extracted_content=f"Successfully saved data to {file_path}")
    except Exception as e:
        return ActionResult(error=f"Failed to save CSV: {str(e)}")

# Add custom function to save cookies
@controller.action("Save cookies to JSON file")
def save_cookies_to_json(cookies_data: str, filename: str) -> str:
    """Save the provided cookies data to a JSON file"""
    try:
        # Create Output directory if it doesn't exist
        output_dir = pathlib.Path("Output")
        output_dir.mkdir(exist_ok=True)
        
        # Parse the cookies data
        try:
            # Try to parse as JSON
            cookies = json.loads(cookies_data)
        except json.JSONDecodeError:
            # If not valid JSON, store as string
            cookies = {"raw_cookies": cookies_data}
        
        # Write to JSON file
        file_path = output_dir / filename
        with open(file_path, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        return ActionResult(extracted_content=f"Successfully saved cookies to {file_path}")
    except Exception as e:
        return ActionResult(error=f"Failed to save cookies: {str(e)}")

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=SecretStr(os.getenv('GEMINI_API_KEY')))

async def main():
    agent = Agent(
        task="""
        You are an Australian Stock trader that can check ASX Stock broker's trade data. Please go to the website https://app.marketlens.com.au/Account/Login?ReturnUrl=%2F,
        enter the username {user_name} to Email address box and password {password} to Password box, then click the Login button. If you are already logged in, then skip the log in process. 
        Then please go to the url https://app.marketlens.com.au/Trades. In this page choose 1D button, and enter LTR in the ASX code box, then click the Refresh button.
        Wait for up to 2 seconds, the data will be shown on the page. Please go through each page and grab the data.
        
        Extract the full trade data(from multiple pages) in a CSV format (comma-separated values) with headers. Then use the custom function "Save data to CSV file" with the extracted data and filename "LTR_1D_trade_data.csv".
        
        After saving the CSV file, use the "extract_cookies" action to extract the cookies from the current page. Then use the custom function "Save cookies to JSON file" with the extracted cookies and filename "marketlens_cookie.json".
        """.format(user_name=os.getenv('MARKETLENS_USERNAME'), password=os.getenv('MARKETLENS_PASSWORD')), 
        llm=llm,
        controller=controller,  # Use our custom controller with the save functions
    )
    result = await agent.run()
    print(result.final_result())
    
asyncio.run(main())