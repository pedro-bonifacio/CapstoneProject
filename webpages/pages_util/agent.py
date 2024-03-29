import pandas as pd
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor
from langchain.agents.agent_toolkits.conversational_retrieval.tool import create_retriever_tool
from langchain.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.tools import PythonAstREPLTool
from langchain.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools.convert_to_openai import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

from webpages.pages_util.template import TEMPLATE
from webpages.pages_util.price_advisor import CustomPredictorTool
from webpages.pages_util.util import DATASET_PATH


class PythonInputs(BaseModel):
    query: str = Field(description="code snippet to run")


def get_chain(conversation_preferences='None'):
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.max_columns", 21)

    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("./webpages/pages_util/FAISS_car_brands_curiosities", embedding_model)
    retriever_tool = create_retriever_tool(vectorstore.as_retriever(), "brand_info_search", "Search for information about a car brand")

    df = pd.read_csv(DATASET_PATH, index_col=0)
    template = TEMPLATE.format(conversation_preferences=conversation_preferences,
                               dcolumns=str(list(df.columns)),
                               dfadvertiser=str(list(df.Advertiser.unique())),
                               dfbrand=str(list(df.Brand.unique())),
                               dffuel=str(list(df.Fuel.unique())),
                               dfsegment=str(list(df.Segment.unique())),
                               dfcolor=str(list(df.Color.unique())),
                               dfgeartype=str(list(df.Gear_Type.unique())),
                               dfcondition=str(list(df.Condition.unique())),
                               dfcomparedprice=str(list(df.Compared_Price.unique())))

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="agent_memory"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    repl = PythonAstREPLTool(
        locals={"df": df},
        name="python_repl",
        description="Runs code and returns the output of the final line",
        args_schema=PythonInputs,
    )

    tools = [repl, CustomPredictorTool(), retriever_tool]

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])
    agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
                "agent_memory": lambda x: x["agent_memory"],
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
    )

    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
    )
    return agent_executor


class AutoMentorChatbot:
    def __init__(self, conversation_preferences='None'):
        self.agent = get_chain(conversation_preferences)
        self.agent_memory = []
        self.chat_history = []

    def generate_response(self, message: str):
        result = self.agent.invoke({'input': message, 'agent_memory': self.agent_memory})
        self.agent_memory.extend(
            [
                HumanMessage(content=message),
                AIMessage(content=result["output"]),
            ]
        )
        if len(self.agent_memory) > 4:
            self.agent_memory = self.agent_memory[-4:]
        return result['output']

    def __str__(self):
        class_name = str(type(self)).split('.')[-1].replace("'>", "")
        return f"🤖 {class_name}."
