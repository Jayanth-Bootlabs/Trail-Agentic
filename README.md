#In the validation_service.py file we will take the user_input and build_validation_graph() is called in the line number 33. 

#Here only the graph is called, that means that graph is just created and the nodes are also created, but nothing is executed still. 

#In the line number 35 a separate thread_id is created for it, thread id is to maintain the what input belongs to which user

#in the line number 41 when you use the graph.ainvoke the nodes are executed, there in the validation_builder.py file the entry point is created and that node is executed and we have created the conditions like what output should go to what node. 

#So when you call the graph.ainvoke() all the nodes in the validation_node are executed. 

#The first node which we set as entry point is validate, so first the validate node is executed, and based on the output of that node, the next node will be executed. 

#So in the validate node function first it will take the prompt and send the user_input. This user_input is taken from the state. 

#Now llm is called and the llm output is stored in the response and response is parsed through the clean_ai_response

#In the state messages field we will update it as validation completed.

#If it is not parsed we will get the status as retry in the "state" and message will be invalida ai response

#If it is parsed we will get the status from the parsed. If we get nothing then it will automatically be "invalid". And same for message also, we will get the message from the parsed if we don't get anything it will be "no response generated."

#the code for the node is written in the validation_node.py file 

#In the validation_builder what is the use of the last line return graph.compile(checkpointer=memory)

#So in the graph/checkpoint.py file we have declared the memorysaver() and stored it in the variable named "memory", so in the every builder file we are calling it at the end right?

#So here the routing will be from the validation_node we are calling the llm and llm will return the output which has status and this status will be updated to the state and validation_transition will read that status and in the validation_builder will read it and choose the conditional_routing. 


# Model Routing

#In the utils/model_router.py file we have written the code for the model routing
#We have written the 3 functions _env_bool, _env_int, _env_float for clean parsing of the .env variables. 
#In the .env file we have written the variables under the #Routing, so whatever we wrote there, we are importing them here in the utils/model_router.py file. 
#Whatever the variables we have written there, python will consider them as strings, so that might cause error here. For some variables in the .env we have declared the values such as True,False and some numbers in integer or decimal forms. 
#But they will be considered as strings in the python so to make sure that they are considered either boolean or float or integer values we are writing these functions and converting them. 

#We have declared the few variables here like 
#Simple model is llama 3.1 and complex model is gpt-oss:120b-cloud
#Temperature means randomness
#Num_predict means number of output tokens
#Keep alive means for how many minutes should the llm be alive since it's been unused.
#Timeout means if the llm doesn't reply in that time period, then it is timeout.
#Json_mode is for agents expect the output in the json mode
#Fallback_to_complex means if any other agent is present other than these, then they should go for complex model

#In the node_tier_map we will define what node should use what model. 

#In the RoutedLLM class we will use all these and in the generate_for_node we will take the prompt and tier will be decided. 
#object is created for this RoutedLLM class and stored in the llm

#So in the every node we will have a line like 
#await llm.generate_for_node(prompt, "validation_node")
#So in the RoutedLLM class we will have this method named generate_for_node, so that method is called everytime a node is being called


# Agent request traces in Grafana

Start the monitoring stack from this directory with `docker compose up -d`. It includes Prometheus, Grafana, Loki, and Promtail. Run or restart the backend after enabling this so it writes JSON logs to `logs/backend.jsonl`; Promtail ships those logs to Loki.

Open Grafana at `http://localhost:3001` and select **Dashboards → Agent Request Traces**. The log panel shows one row per LLM call with its timestamp, trace ID, pipeline run ID (when run through the orchestrator), agent, model, tier, status, latency, and request preview. The other panels show call counts and p95 latency over the selected time range. Use **Explore → Loki** with `{job="backend", event="llm_request"} | json | pipeline_run_id="19"` to filter to a particular run ID.

Request previews are included by default and truncated to 2,000 characters. Set `LLM_TRACE_INCLUDE_QUERY=false` in `.env` and restart the backend to omit them. Per-call logs are also written locally under `logs/`; that directory is excluded from Git. Loki retains ingested logs for seven days.


# Redis



# Taking an example

Let’s use a validation request such as: “Build me a task tracking web app with user accounts and project boards.”
How transition.py routes the result
The service starts the validation graph with state similar to:
{
    "user_input": "Build me a task tracking web app with user accounts and project boards.",
    "retry_count": 0
}
The graph starts at the validate node. That node asks the LLM to assess the input and returns an updated state with a status, such as "valid", "clarify", "invalid", or "retry".
In [transition.py (line 4)](/Users/nissankararaojayanth/Desktop/Trail_Agentic/data_pipeline_generator_backend/graph/transition.py:4), validation_transition reads that status:
def validation_transition(state):
    return state.get("status", "invalid")
Then the conditional edges in [validation_builder.py (line 22)](/Users/nissankararaojayanth/Desktop/Trail_Agentic/data_pipeline_generator_backend/builder/validation_builder.py:22) choose what runs next:
Status returned by validation	Next node
"valid"	End the graph
"clarify"	Run clarification_node, then end
"invalid"	Run rejection_node, then end
"retry"	Run retry_node, then try validation again


For example, if the LLM returns "clarify", the path is:
validate → clarification_node → END
The clarification node adds the question to the state’s messages. The graph then ends and the service saves the result. If the LLM response could not be parsed, validation returns "retry" instead, so the graph follows the retry path.
retry_transition handles what happens after retry_node increments retry_count. If the count is below the limit, it returns "retry" and the builder routes back to validation. Once the limit is reached, it returns "failed" and the builder sends execution to rejection_node.
What checkpoint.py does
[checkpoint.py (line 1)](/Users/nissankararaojayanth/Desktop/Trail_Agentic/data_pipeline_generator_backend/graph/checkpoint.py:1) creates a LangGraph MemorySaver:
memory = MemorySaver()
The validation builder passes that saver into graph.compile(checkpointer=memory). When ainvoke() runs, LangGraph can use the saver to checkpoint graph state for the invocation’s thread_id.
The validation service supplies a unique thread ID, for example:
"validation-42-a1b2c3..."
LangGraph uses that ID as the key for the graph’s checkpoint data. Conceptually, it’s like a label saying, “these checkpoints belong to this graph thread.” It does not by itself authenticate user 42 or manage access to the request.
MemorySaver stores checkpoints in the backend process’s memory. It is useful for checkpointing while the process is running, but it is not durable storage: restarting the backend clears it. The validation service separately saves the final validation result in the database.
Putting it together
Service creates initial state and thread_id
              ↓
graph.ainvoke(state, config)
              ↓
validate node calls the LLM and updates state
              ↓
validation_transition reads state["status"]
              ↓
Builder selects the matching next node
              ↓
LangGraph checkpoints graph state under thread_id
              ↓
Graph ends; service saves the result to the database
So, transition.py determines which path the graph follows, while checkpoint.py provides temporary saved graph state associated with a thread ID.

## Running unit tests

The unit tests are in `tests/unit` and use pytest. From the backend directory, install the test extra and run the suite:

```bash
pip install -e ".[test]"
python -m pytest tests/unit -v
```


# graph/state.py

#Why do we need a state?
#- We need a state because the agents will talk to each other using this state. 
- Agents shouldn't communicate with each other directly, agents should communicate with each other through a shared state.
- Agents will update this shared state and other agents will read from this shared state.
- Why the agents shouldn't talk with each other means if they talk with each other directly, then it becomes difficult for us for debugging. 
- Agent A need not to know that Agent B exists what inputs does Agent B need. Agent A will just take the input from the shared state and will update the output to the shared state and Agent B will again take the input from the shared state.


- Here TypedDict documents the expected keys and value types and helps type checkers catch mistakes. It does not enforce at runtime that no other keys can be added to the dictionary, and total=False means every key in GraphState is optional. A node or graph invocation can use only the fields it needs. It doesn’t mean a key must be updated each time.
