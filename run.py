import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# 加载环境变量
load_dotenv()

from src.agent.graph import build_invest_graph

def main():
    print("构建投研 Agent 图 (支持多轮对话)...")
    app = build_invest_graph()
    
    # 配置会话 ID
    config = {"configurable": {"thread_id": "user_session_1"}}
    
    print("\\n=======================================================")
    print("欢迎使用投研分析 Agent！您可以输入自然语言进行对话查询。")
    print("输入 'quit' 或 'exit' 退出对话。")
    print("=======================================================\\n")
    
    while True:
        try:
            query = input("User > ")
            if query.lower() in ['quit', 'exit']:
                print("再见！")
                break
                
            if not query.strip():
                continue
                
            # 每次输入新的消息时，我们将用户的 query 存入 messages 历史，并更新 query 字段
            # 注意 messages 是 Annotated[list, add_messages]，会自动与现有历史拼接
            input_state = {
                "query": query,
                "messages": [HumanMessage(content=query)],
            }
            
            print("Agent 正在思考处理中...")
            for output in app.stream(input_state, config=config):
                for key, value in output.items():
                    if "error" in value and value["error"]:
                        print(f"  [节点 {key} 报警]: {value['error']}")
                    else:
                        if key == "report_node":
                            print("\\n============ 分析回复 ============")
                            print(value.get("final_report", ""))
                            print("==================================\\n")
                        else:
                            # 调试信息可看情况是否打开
                            # print(f"  [节点完成]: {key}")
                            pass
                            
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\\n会话中止。")
            break
        except Exception as e:
            print(f"\\n[执行出错]: {e}")

if __name__ == "__main__":
    main()
