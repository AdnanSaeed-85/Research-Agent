from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from CONFIG import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER

DB_PATH = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"

def load_from_store(DB_PATH)
    with PostgresStore.from_conn_string(DB_PATH) as store:
        all_data = store.search("")
        for data in all_data:
            # print(f"{data.namespace} | {data.value['data']}")
        
            return data.namespace, data.value


def load_from_sever(DB_PATH):
    with PostgresSaver.from_conn_string(DB_PATH) as saver:
        checkpoints = saver.list({})
        
        for cp in checkpoints:
            thread_id = cp.config['configurable']['thread_id']
            messages = cp.checkpoint['channel_values'].get('messages', [])
            for msg in messages:
                # print(f"{msg.__class__.__name__}: {msg.content}")
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # print(f"Tools: {msg.tool_calls}")
                    return msg.tool_calls
                return msg._class__.__name__, msg.content
            return thread_id