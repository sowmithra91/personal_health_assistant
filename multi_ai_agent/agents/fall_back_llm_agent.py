from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from utilities.llm_provider import llm

load_dotenv()

class FallBackLLMAgent:
    def __init__(self, llm: BaseChatModel, tools_json: dict = {}, agents: list= []):
        self.llm = llm
        self.fall_back_graph = self.create_fallback_llm_graph_with_memory()
        self.agents = agents
        self.tools_json = tools_json
        self.system_prompt = f"""You are a helpful assistant with agents: {self.agents} and tools: {tools_json}.
        ### Interaction Guidelines:
        - Confirm successful tool execution.
        - Suggest relevant follow-up operations.
        - Encourage exploring all tools.
        """

    async def llm_node(self, state: MessagesState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        message = await self.llm.ainvoke(messages)
        state["messages"] = [message]
        return state

    def create_fallback_llm_graph_with_memory(self):
        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("llm_node", self.llm_node)

        graph_builder.add_edge(START, "llm_node")
        graph_builder.add_edge("llm_node", END)

        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        return graph
    
llm_graph_agent_object = FallBackLLMAgent(llm=llm)
llm_graph_agent = llm_graph_agent_object.fall_back_graph