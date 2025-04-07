from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from typing import Literal, List
from typing_extensions import TypedDict
import os
from dotenv import load_dotenv
from utilities.llm_provider import llm

# Assuming these are imported from their respective files
from agents.restaurant_agent import RestaurantAgent
from agents.health_profile_agent import HealthProfileAgent
from agents.fall_back_llm_agent import FallBackLLMAgent
import logging
from agents.prompts import restaurant_agent_prompt, health_profile_agent_prompt, diet_recommender_agent_prompt
from langgraph.prebuilt import create_react_agent
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

class CustomAgentState(MessagesState):
    next: Optional[str] = None
    chain_of_thought: Optional[List[str]] = []

class Router(TypedDict):
    """
    Worker to route to next. If no workers needed or identified, strictly route to FINISH.
    
    Attributes:
        next: The next worker to route to.
        chain_of_thought: A list of strings representing the chain of thought.
    """
    next: Literal["Restaurant_Order_Worker", "Health_Profile_Worker", "Diet_Recommender_Worker", "General_LLM_Worker", "FINISH"]
    chain_of_thought: List[str]

class HealthyDietSupervisorAgent:
    def __init__(self):
        self.llm = llm
        self.members = ["Restaurant_Order_Worker", "Health_Profile_Worker", "Diet_Recommender_Worker", "General_LLM_Worker"]
        self.restaurant_agent_object = RestaurantAgent(llm, restaurant_agent_prompt)
        self.health_profile_agent_object = HealthProfileAgent(llm, health_profile_agent_prompt)
        self.diet_recommender_agent = create_react_agent(
            model=llm,
            tools=[],  # No tools as per your request
            prompt=diet_recommender_agent_prompt
        )

        self.combined_tools = [self.restaurant_agent_object.tools, self.health_profile_agent_object.tools, [], []]
        self.tools_json = self.generate_tools_json()
        self.fall_back_llm_agent_object = FallBackLLMAgent(llm=llm, tools_json=self.tools_json, agents=self.members)
        self.restaurant_agent_object.fromat_system_prompt(agents=self.members, tools_json=self.tools_json)
        self.health_profile_agent_object.fromat_system_prompt(agents=self.members, tools_json=self.tools_json)
        self.system_prompt = (
            "You are a supervisor tasked with managing a conversation between workers. Your job is to understand the user input, analyze their intention, and select the appropriate worker to proceed. "
            f"Available workers: {self.members} with the following tools respectively: {self.tools_json}. "
            "Each worker will perform their task and return their results and status to you. "
            "Based on the user request, follow these steps:\n"
            "1. Analyze the user input and determine their intent.\n"
            "2. Match the intent to a worker’s capabilities based on their tools and expertise.\n"
            "3. If a specialized worker matches, select them as the next worker.\n"
            "4. If the task is complete or no further action is needed, select 'FINISH'.\n"
            "5. If the user prompt doesn’t match a specialized worker’s capabilities, select 'General_LLM_Worker'.\n"
            "Provide your reasoning as a list of concise steps (chain of thought).\n"
        )
        self.supervisor_graph_agent = self.create_supervisor_graph_agent()

    async def generate_tools_json(self):
        tools_json = {}
        for worker, tools in zip(self.members, self.combined_tools):
            tools_json[worker] = []
            for tool in tools:
                tool_info = {
                    "name": tool.__name__,
                    "description": tool.__doc__
                }
                tools_json[worker].append(tool_info)
        return tools_json

    async def supervisor_node(self, state: CustomAgentState) -> CustomAgentState:
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        response = await self.llm.with_structured_output(Router).ainvoke(messages)
        logger.info("resonse"+ str(response))
        if response == None:
            goto = "FINISH"
        else:
            if "chain_of_thought" not in state:
                state["chain_of_thought"] = []
            if "chain_of_thought" in response:
                state["chain_of_thought"] = response["chain_of_thought"]
            goto = response.get("next", END)
        if goto == "FINISH":
            if "next" not in state or state["next"] == END:
                goto = "General_LLM_Worker"
            else:
                goto = END
        state["next"] = goto
        return state

    async def call_restaurant_agent(self, state: CustomAgentState) -> CustomAgentState:
        return await self.restaurant_agent_object.restaurant_graph_agent.ainvoke({"messages": state["messages"]})

    async def call_health_profile_agent(self, state: CustomAgentState) -> CustomAgentState:
        return await self.health_profile_agent_object.health_graph_agent.ainvoke({"messages": state["messages"]})
    
    async def call_health_reviewer_agent(self, state: CustomAgentState) -> CustomAgentState:
        return await self.diet_recommender_agent.ainvoke({"messages": state["messages"]})

    async def call_fall_back_agent(self, state: CustomAgentState) -> CustomAgentState:
        return await self.fall_back_llm_agent_object.fall_back_graph.ainvoke({"messages": state["messages"]})

    def create_supervisor_graph_agent(self):
        supervisor_builder = StateGraph(CustomAgentState)

        # Add the supervisor node
        supervisor_builder.add_node("supervisor", self.supervisor_node)

        # Add the worker nodes
        supervisor_builder.add_node("Restaurant_Order_Worker", self.call_restaurant_agent)
        supervisor_builder.add_node("Health_Profile_Worker", self.call_health_profile_agent)
        supervisor_builder.add_node("Diet_Recommender_Worker", self.call_health_reviewer_agent)
        supervisor_builder.add_node("General_LLM_Worker", self.call_fall_back_agent)

        # Define the control flow
        supervisor_builder.add_edge(START, "supervisor")
        supervisor_builder.add_conditional_edges("supervisor", lambda state: state["next"])
        supervisor_builder.add_edge("Restaurant_Order_Worker", "supervisor")
        supervisor_builder.add_edge("Health_Profile_Worker", "supervisor")
        supervisor_builder.add_edge("Diet_Recommender_Worker", "supervisor")
        supervisor_builder.add_edge("General_LLM_Worker", END)

        # Compile the supervisor graph
        supervisor_graph = supervisor_builder.compile(checkpointer=MemorySaver())
        return supervisor_graph

# Instantiate the HealthyDietSupervisorAgent
healthy_diet_supervisor = HealthyDietSupervisorAgent()
supervisor_graph_agent = healthy_diet_supervisor.supervisor_graph_agent