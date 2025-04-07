import streamlit as st
import google.generativeai as genai
import pathlib
import textwrap
import pandas as pd


# data
url1 = "https://raw.githubusercontent.com/aritsarann/chat_with_gemini/refs/heads/main/transactions.csv"
url2 = "https://raw.githubusercontent.com/aritsarann/chat_with_gemini/refs/heads/main/data_dict.csv"

transaction_df = pd.read_csv(url1)
data_dict_df = pd.read_csv(url2)

df_name = 'transaction_df'
example_record = transaction_df.head(2).to_string()
data_dict_text = '\n'.join('- ' + data_dict_df['column_name'] +
                           ': ' +data_dict_df['data_type'] +
                           '. ' +data_dict_df['description'])


st.title('🔍 LiquorLens: Insight on Tap')
st.markdown(""" 
This system is designed to assist you with detailed insights on liquor sales transactions, inventory, and vendor performance.
""")
# Display an expandable section (accordion) for Data Overview
with st.expander("**📊 Data Snapshot**"):
    st.markdown("""
    This dataset (CSV file) contains transaction data with the following columns:
      - `invoice_and_item_number`: Unique identifier for each product in the store order.
      - `date`: Date of the transaction.
      - `store_name`: Name of the store.
      - `city`: The city where the store is located.
      - `category_name`: Category of the liquor.
      - `vendor_name`: Vendor's name of the liquor product.
      - `state_bottle_retail`: The cost per bottle of the liquor.
      - `bottles_sold`: The number of bottles sold.
      - `sale_dollars`: Total amount for the sale (number of bottles * cost per bottle).
    """)
    st.markdown("**Sample Data:**")
    st.write(transaction_df.head(4))


try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    if "chat" not in st.session_state:
        st.session_state.chat = []


    def role_to_streamlit(role:str) -> str:
        if role == 'model':
            return 'assistant'
        else:
            return role

    for role, message in st.session_state.chat:
        st.chat_message(role).markdown(message)

    if question := st.chat_input("Ask your question here, e.g. 'What is the total sales in January 2025?'"):
        st.session_state.chat.append(('user', question))
        st.chat_message('user').markdown(question)

        prompt_template = f"""
        You are a helpful Python code generator. 
        Your goal is to write Python code snippets based on the user's question 
        and the provided DataFrame information.

        Here's the context:

        **User Question:**
        {question}

        **DataFrame Name:**
        {df_name}

        **DataFrame Details:**
        {data_dict_text}

        **Sample Data (Top 2 Rows):**
        {example_record}

        **Instructions:**
        1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
        2. **Crucially, use the `exec()` function to execute the generated code.**
        3. Do not import pandas
        4. Change date column type to datetime
        5. **Store the result of the executed code in a variable named `ANSWER`.** 
        This variable should hold the answer to the user's question (e.g., a filtered DataFrame, a calculated value, etc.).
        6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`. Do not include code to load the DataFrame.
        7. Keep the generated code concise and focused on answering the question.
        8. If the question requires a specific output format (e.g., a list, a single value), ensure the `query_result` variable holds that format.

        **Example:**
        If the user asks: "Show me the rows where the 'age' column is greater than 30."
        And the DataFrame has an 'age' column.

        The generated code should look something like this (inside the `exec()` string):

        ```python
        query_result = {df_name}[{df_name}['age'] > 30]
        """

        prompt = prompt_template.format(
            question=question,
            df_name=df_name,
            data_dict_text=data_dict_text,
            example_record=example_record
        )
        code_response = model.generate_content(prompt)
        code_text = code_response.text.replace("```", "#")  
        exec(code_text)  # รันโค้ดที่ถูกสร้างขึ้นจากโมเดล

        try:
        # STEP 2: Execute the Python code and generate result
            exec(code_text)

            explain_the_results = f'''
            the user asked {question}, 
            here is the results {ANSWER}
            
            Now, provide a professional answer based on the data.
            - Summarize the result clearly.
            - Offer meaningful business insight or interpretation.
            - Suggest potential actions or strategies.
            - If relevant, mention patterns, anomalies, or recommendations.

            Keep the tone analytical but friendly, like a smart assistant.
            '''
        except Exception as e:
            st.error(f"❌ Error while executing generated code: {e}")

        response = model.generate_content(explain_the_results)
        bot_response = response.text
        st.session_state.chat.append(('assistant', bot_response))
        st.chat_message('assistant').markdown(bot_response)

    
except Exception as e :
    st.error(f'An error occurred {e}')


# How many total sale in jan 2025?
