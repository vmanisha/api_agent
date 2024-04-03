Notebook Summary
-----------------

Ipython notebook showing the following:

a) indexing of an api using url
b) Taking a user input query:
  -- finding the most relevant API function calls that may answer user's query
  -- Provide LLM information about the functions and ask it to create a plan. 
  -- Execute the plan (these functions wont work as there is no real api atm)
  -- Finally LLM reviews the results of the API calls to generate final answer. 

Constraints
-----------

1. The conversation will not gracefully degrade as some more implementation is required to process outputs of API function executions, corner cases of llm hallucination etc.
2. While all the functions across different APIs have been indexed together, we need to add URL for each of these APIs to be able to call them realtime.
3. LangChain has some tooling around agents, APIs and tools. However, I found it to be severely limited and given the limited time, I chose to use simple constructs and build a MVP.
4. Searching is only going to work on APIs that have good documentation. Making sense of Ad-Hoc function names and matching them to user queries will not be possible currently.
5. Finally, I did not use the schemas too extensively. But we can use them to check LLM outputs, also populate them for LLM to answer questions better.
