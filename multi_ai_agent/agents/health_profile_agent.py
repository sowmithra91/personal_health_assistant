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

# Load health profile from mock JSON file
with open("mock/user_health_profile.json", "r") as file:
    health_profile = json.load(file)

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

class HealthProfileAgent:
    def __init__(self, llm: BaseChatModel, health_profile_agent_prompt: str):
        self.llm = llm
        self.tools = [
            get_current_conditions,
            get_past_conditions,
            get_dietary_restrictions
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.health_graph_agent = self.create_health_graph_agent()
        self.health_system_prompt = health_profile_agent_prompt
        self.agents = []
        self.tools_json = {}

    async def fromat_system_prompt(self, agents, tools_json):
        self.agents = agents
        self.tools_json = tools_json
        self.health_system_prompt = self.health_system_prompt.format(agents=agents,tools_json=tools_json)

    async def health_tool_calling_llm(self, state: MessagesState):
        system_message = HumanMessage(
            content=self.health_system_prompt
        )
        message = await self.llm_with_tools.ainvoke([system_message] + state['messages'])
        state['messages'] = [message]
        return state

    def create_health_graph_agent(self):
        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("tool_calling_llm", self.health_tool_calling_llm)
        graph_builder.add_node("tools", ToolNode(self.tools))

        graph_builder.add_edge(START, "tool_calling_llm")
        graph_builder.add_conditional_edges("tool_calling_llm", tools_condition)
        graph_builder.add_edge("tools", "tool_calling_llm")
        
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        return graph

# Create the health profile agent instance
#health_agent_object = HealthProfileAgent(llm)
#health_graph_agent = health_agent_object.health_graph_agent