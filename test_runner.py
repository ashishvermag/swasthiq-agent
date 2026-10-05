import os
import json
import time
import requests

def run_adversarial_tests():
    url = "http://127.0.0.1:8000/agent/run"
    conv_dir = "conversations"
    
    if not os.path.exists(conv_dir):
        print(f"Error: '{conv_dir}' directory not found.")
        return

    print("Running Live Agent Logic Tests...\n")
    
    for filename in sorted(os.listdir(conv_dir)):
        if not filename.endswith(".json"):
            continue
            
        with open(os.path.join(conv_dir, filename), "r") as f:
            test_case = json.load(f)
            
        print(f"Running {test_case['id']} - {test_case['description']}")
        payload = {
            "conversation_id": test_case["id"],
            "today": test_case["today"],
            "turns": test_case["turns"]
        }

        # Retry loop to gracefully bypass 503s and 429s
        for attempt in range(5):
            try:
                response = requests.post(url, json=payload)
                result = response.json()
                
                # If the backend caught an API error, wait and retry
                if "System encountered an error" in result.get("reply", ""):
                    print(f"  [!] API limit hit. Waiting 15 seconds to clear quota (Attempt {attempt+1}/5)...")
                    time.sleep(15)
                    continue
                
                # Evaluate against expected outcomes
                expected = test_case["expected"]
                state_match = result["terminal_state"] == expected["terminal_state"]
                
                expected_reason = expected.get("escalation_reason")
                actual_reason = result.get("escalation_reason")
                reason_match = actual_reason == expected_reason
                
                executed_tools = [t["name"] for t in result.get("tool_calls", [])]
                must_call_pass = all(tool in executed_tools for tool in expected.get("must_call", []))
                must_not_call_pass = all(tool not in executed_tools for tool in expected.get("must_not_call", []))

                if state_match and reason_match and must_call_pass and must_not_call_pass:
                    print(f"  ✅ PASS")
                else:
                    print(f"  ❌ FAIL")
                    if not state_match:
                        print(f"     Expected State: {expected['terminal_state']}, Got: {result['terminal_state']}")
                    if not reason_match:
                        print(f"     Expected Reason: {expected_reason}, Got: {actual_reason}")
                    if not must_call_pass:
                        print(f"     Expected tools to call: {expected.get('must_call')}, Actually called: {executed_tools}")
                    if not must_not_call_pass:
                        print(f"     Forbidden tools called! Called: {executed_tools}")
                print("-" * 40)
                break 
                
            except Exception as e:
                print(f"  [!] Connection failed: Is Uvicorn running? Error: {e}")
                break

        # Mandatory wait between successful tests to stay under 5 Requests Per Minute
        time.sleep(15)

if __name__ == "__main__":
    run_adversarial_tests()