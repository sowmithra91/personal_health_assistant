from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
import json
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from utilities.llm_provider import llm  # Assuming this is your LLM provider

load_dotenv()

# Mock menu data (in real scenario, this would be loaded from a JSON file)
with open("mock/south_indian_veg_menu.json", "r") as file:
    menu_data = json.load(file)

# Store orders in memory (simulating a database)
orders_history = []

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

class RestaurantAgent:
    def __init__(self, llm: BaseChatModel, restaurant_agent_prompt:str):
        self.llm = llm
        self.tools = [
            get_menu,
            place_order,
            get_order_history
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.restaurant_graph_agent = self.create_restaurant_graph_agent()
        self.restaurant_system_prompt = restaurant_agent_prompt
        self.agents = []
        self.tools_json = {}

    async def fromat_system_prompt(self, agents, tools_json):
        self.agents = agents
        self.tools_json = tools_json
        self.restaurant_system_prompt = self.restaurant_system_prompt.format(agents=agents,tools_json=tools_json)

    async def restaurant_tool_calling_llm(self, state: MessagesState):
        system_message = HumanMessage(
            content=self.restaurant_system_prompt
        )
        message = await self.llm_with_tools.ainvoke([system_message] + state['messages'])
        state['messages'] = [message]
        return state

    def create_restaurant_graph_agent(self):
        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("tool_calling_llm", self.restaurant_tool_calling_llm)
        graph_builder.add_node("tools", ToolNode(self.tools))

        graph_builder.add_edge(START, "tool_calling_llm")
        graph_builder.add_conditional_edges("tool_calling_llm", tools_condition)
        graph_builder.add_edge("tools", "tool_calling_llm")
        
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        return graph

# Create the restaurant agent instance
#restaurant_agent_object = RestaurantAgent(llm)
#restaurant_graph_agent = restaurant_agent_object.restaurant_graph_agent