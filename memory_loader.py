from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from CONFIG import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER
DB_PATH = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"

# def load_from_store(DB_PATH):
#     with PostgresStore.from_conn_string(DB_PATH) as store:
#         all_data = store.search("")
#         for data in all_data:
#             print(f"{data.namespace} | {data.value['data']}")
    
#     print()
#     print("----------------------------------------------------------------")
#     print()


# with PostgresSaver.from_conn_string(DB_PATH) as saver:
#     checkpoints = saver.list({})
    
#     thread = []
#     for cp in checkpoints:
#         print(cp)
#         thread_id = cp.config['configurable']['thread_id']
#         if thread_id not in thread:
#             thread.append(thread_id)
#         messages = cp.checkpoint['channel_values'].get('messages', [])
#         for msg in messages:
#             # print(f"{msg.__class__.__name__}: {msg.content}")
#             if hasattr(msg, 'tool_calls') and msg.tool_calls:
#                 pass
#                 # print(f"Tools: {msg.tool_calls}")
#     print(thread)
    

def fetch_all_users_and_threads():
    user_thread_map = set()

    print("--- Connecting to Database ---")
    
    with PostgresSaver.from_conn_string(DB_PATH) as saver:
        # List ALL checkpoints
        checkpoints = saver.list({})
        
        for check in checkpoints:
            # 1. Get Thread ID from Config (Reliable)
            config = check.config.get("configurable", {})
            thread_id = config.get("thread_id")
            
            if not thread_id:
                continue

            # 2. Look for User Name in TWO places
            # Priority A: Check 'configurable' (New method)
            user_name = config.get("user_name")
            
            # Priority B: Check 'metadata' (Old method / Automatic)
            if not user_name:
                user_name = check.metadata.get("user_name")
            
            # Priority C: Fallback
            if not user_name:
                user_name = "Unknown User"

            user_thread_map.add((user_name, thread_id))

    print(f"\n--- Found {len(user_thread_map)} Unique Threads ---")
    print(f"{'USER NAME':<25} | {'THREAD ID'}")
    print("-" * 45)
    
    for user, thread in sorted(list(user_thread_map)):
        print(f"{user:<25} | {thread}")

if __name__ == "__main__":
    fetch_all_users_and_threads()