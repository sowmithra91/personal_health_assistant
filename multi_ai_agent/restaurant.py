from mcp.server.fastmcp import FastMCP
import json

# Initialize FastMCP server
mcp = FastMCP("restaurant_mcp_server")

# Mock menu data
with open("mock/south_indian_veg_menu.json", "r") as file:
    menu_data = json.load(file)

# Store orders in memory (simulating a database)
orders_history = []

@mcp.tool()
async def get_menu() -> dict:
    """
    This function retrieves the South Indian vegetarian restaurant menu.
    Output:
        menu_data: dict containing menu items
    """
    try:
        return {"status": True, "data": menu_data}
    except Exception as e:
        return {"status": False, "data": f"Error fetching menu: {str(e)}"}

@mcp.tool()
async def place_order(order_items: list, is_diet_recommended: bool = False) -> dict:
    """
    This function places an order with the specified items.
    Args:
        order_items: list of dicts containing item_id and quantity
        is_diet_recommended: is the items in the order are recommended?
    Output:
        order_confirmation: dict with order details
    """
    try:
        if not is_diet_recommended:
            return {"status": False, "data": "The ordered items are not recommended for you diet, please order the recommended items based on you health."}
        # Validate items against menu
        available_items = {item["id"]: item for item in menu_data["items"]}
        order_total = 0
        order_details = []
        
        for order_item in order_items:
            item_id = order_item.get("item_id")
            quantity = order_item.get("quantity", 1)
            
            if item_id not in available_items:
                return {"status": False, "data": f"Item {item_id} not found in menu"}
            
            item = available_items[item_id]
            item_total = item["price"] * quantity
            order_total += item_total
            order_details.append({
                "item_id": item_id,
                "name": item["name"],
                "quantity": quantity,
                "price": item["price"],
                "total": item_total
            })
        
        order_id = f"ORD{len(orders_history) + 1:04d}"
        order = {
            "order_id": order_id,
            "items": order_details,
            "total_amount": order_total,
            "timestamp": "2025-04-01"  # Using current date from your context
        }
        
        orders_history.append(order)
        return {
            "status": True,
            "data": {
                "order_id": order_id,
                "message": "Order placed successfully",
                "details": order
            }
        }
    except Exception as e:
        return {"status": False, "data": f"Error placing order: {str(e)}"}

@mcp.tool()
async def get_order_history() -> dict:
    """
    This function retrieves all previous orders.
    Output:
        orders_history: dict containing all past orders
    """
    try:
        if not orders_history:
            return {"status": True, "data": "No orders placed yet"}
        return {"status": True, "data": orders_history}
    except Exception as e:
        return {"status": False, "data": f"Error fetching order history: {str(e)}"}


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')