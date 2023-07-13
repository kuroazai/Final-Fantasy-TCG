from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory


class AIAgent:

    def __init__(self):
        self.chain = None
        self.model = self.model = OpenAI(openai_api_key='YOUR_API_KEY',
                                         temperature=0)

    @staticmethod
    def set_context_prompt(prompt):
        return PromptTemplate(input_variables=["history", "human_input"],
                              template=prompt,
                              return_only_outputs=True,)

    def set_model_chain(self, prompt):
        prompt = self.set_context_prompt(prompt)

        self.chain = LLMChain(llm=self.model,
                                    prompt=prompt,
                                    verbose=False,
                                    memory=ConversationBufferWindowMemory(k=2),
                                    )

    def on_message(self, message):
        return self.chain.run(human_input=message)

