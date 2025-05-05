from mcp.server.fastmcp import FastMCP
import json

# Initialize FastMCP server
mcp = FastMCP(name="health_profile_mcp", port=8001)

# Load health profile from mock JSON file
with open("mock/user_health_profile.json", "r") as file:
    health_profile = json.load(file)

@mcp.tool()
async def get_current_conditions() -> dict:
    """
    This function retrieves the user's current health conditions.
    Output:
        current_conditions: dict containing current health conditions
    """
    try:
        current_conditions = health_profile["user_health_profile"]["current_conditions"]
        return {"status": True, "data": current_conditions}
    except Exception as e:
        return {"status": False, "data": f"Error fetching current conditions: {str(e)}"}

@mcp.tool()
async def get_past_conditions() -> dict:
    """
    This function retrieves the user's past health conditions.
    Output:
        past_conditions: dict containing past health conditions
    """
    try:
        past_conditions = health_profile["user_health_profile"]["past_conditions"]
        return {"status": True, "data": past_conditions}
    except Exception as e:
        return {"status": False, "data": f"Error fetching past conditions: {str(e)}"}

@mcp.tool()
async def get_dietary_restrictions() -> dict:
    """
    This function compiles all dietary restrictions based on current and past conditions.
    Output:
        restrictions: dict with combined dietary restrictions
    """
    try:
        current_restrictions = []
        past_restrictions = []
        
        # Get restrictions from current conditions
        for condition in health_profile["user_health_profile"]["current_conditions"]:
            current_restrictions.extend(condition["restrictions"])
        
        # Get restrictions from past conditions (might still be relevant)
        for condition in health_profile["user_health_profile"]["past_conditions"]:
            past_restrictions.extend(condition["restrictions"])
        
        combined_restrictions = {
            "current_restrictions": list(set(current_restrictions)),  # Remove duplicates
            "past_restrictions": list(set(past_restrictions)),      # Remove duplicates
            "all_restrictions": list(set(current_restrictions + past_restrictions))
        }
        
        return {"status": True, "data": combined_restrictions}
    except Exception as e:
        return {"status": False, "data": f"Error fetching dietary restrictions: {str(e)}"}
    
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')