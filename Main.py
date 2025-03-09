import ray

import logging
from typing import List, Dict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
#from huggingface_hub import InferenceClient
from langchain_core.runnables import Runnable
from langchain_core.tools import tool
import requests 

# 設定 Hugging Face API
#HF_API_KEY = ""
#HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
#client = InferenceClient(model=HF_MODEL, token=HF_API_KEY)

ray.init(address="ray://host.docker.internal:10001", namespace="default")
client = ray.get_actor("model_worker")

BASE_URL = "https://k6oayrgulgb5sasvwj3tsy7l7u0tikfd.lambda-url.ap-northeast-1.on.aws/api/v3/tools"
HEADERS = {"Authorization": "Key"}
# 旅宿
@tool
def get_taiwan_counties():
    """取得台灣所有縣市 ID & 名稱"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/counties"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def get_taiwan_districts(county_id: int):
    """取得指定縣市內的鄉鎮區 ID & 名稱"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/districts?county_id={county_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def get_hotel_types():
    """取得飯店類型 (例如: 商務旅館、民宿、豪華飯店)"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel_group/types"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def get_hotel_facilities():
    """取得飯店設施清單 (例如: 免費WiFi、泳池、停車場)"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/facilities"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def get_room_facilities():
    """取得房間內可用設施 (例如: 冷氣、電視、浴缸)"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/room_type/facilities"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def get_bed_types():
    """取得房間床型 (例如: 雙人床、單人床、上下舖)"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/room_type/bed_types"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# 旅館
@tool
def search_hotels(county_id: int, district_id: int = None, min_price: int = 0, max_price: int = 10000):
    """根據縣市、鄉鎮、價格篩選飯店"""
    params = {"county_ids": [county_id], "district_ids": [district_id], "lowest_price": min_price, "highest_price": max_price}
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotels"
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

@tool
def fuzzy_match_hotel(hotel_name: str):
    """模糊搜尋飯店名稱，找出最接近的結果"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/fuzzy_match?query={hotel_name}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def get_hotel_details(hotel_id: int):
    """查詢指定飯店的詳細資訊"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/detail?hotel_id={hotel_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def search_hotels_by_facility(facility_id: int):
    """根據飯店設施搜尋符合條件的旅館 (如: 含泳池的飯店)"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/supply?facility_id={facility_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def search_hotel_plans(hotel_id: int, keyword: str):
    """根據關鍵字查詢指定飯店的可訂購方案 (如: 含早餐、免費停車)"""
    url = f"{BASE_URL}/interview_test/taiwan_hotels/plans?hotel_id={hotel_id}&keyword={keyword}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

@tool
def check_hotel_vacancies(county_id: int, check_in: str, check_out: str, adults: int, children: int):
    """查詢可訂房的飯店 (需輸入入住日期、退房日期、成人/兒童人數)"""
    params = {
        "county_ids": [county_id],
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "children": children
    }
    url = f"{BASE_URL}/interview_test/taiwan_hotels/hotel/vacancies"
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

# 景點
@tool
def search_nearby_places(query: str):
    """查詢指定地點周邊的商店、餐廳、捷運站等"""
    url = f"{BASE_URL}/external/gcp/places/nearby_search_with_query"
    params = {"text_query": query}
    response = requests.post(url, headers=HEADERS, json=params)
    return response.json()


# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定義狀態結構
class State(BaseModel):
    city: str
    messages: List[Dict] = Field(default_factory=list)
    hotel_recommendations: str = ""
    travel_plan: str = ""
    analysis_report: str = ""

# 解讀用戶需求agent
class PrimaryAdvisor(Runnable):
    def invoke(self, state: State, config=None) -> State:
        user_query = state.messages[-1].content
        prompt = prompt = f"""
        請將以下用戶的旅遊需求轉換為 JSON 格式，**確保輸出只有 JSON**，不要包含任何額外的解釋或建議。

        ### **JSON 輸出格式範例**
        {{
        "county": "台中市",
        "check_in": "2025-01-01",
        "check_out": "2025-01-03",
        "adults": 3,
        "children": 2,
        "lowest_price": 1000,
        "highest_price": 5000
        }}

        ---
        **用戶需求：**
        {user_query}

        ⚠️ **請注意**
        1. **請嚴格遵守 JSON 格式**，不得加入任何額外文字
        2. **請直接輸出 JSON**，不要添加 Markdown 代碼塊 (例如 ```json )
        """
        response = ray.get(client.generate.remote(prompt))
        logger.info(f"Parsed user query: {response}")
        
        # 假設解析結果返回一個 JSON 格式的資料，包含 city、budget 等資訊
        parsed_data = eval(response)  # 請根據實際回應格式進行解析
        state.city = parsed_data.get("city", state.city)
        
        # 使用 tools 來獲取額外的資訊
        county_data = get_taiwan_counties()
        state.messages.append({"role": "system", "content": f"獲取縣市數據: {county_data}"})
        
        return state



# 旅館agent
class HotelAdvisor(Runnable):
    def invoke(self, state: State, config=None) -> State:
        city = state.city
        prompt = f"請推薦{city}的最佳飯店，考慮價格和評價"
        #response = ray.get(client.text_generation(prompt, max_new_tokens=500))
        response = ray.get(client.generate.remote(prompt))
        logger.info(f"Hotel Recommendations Generated: {response}")

        # 更新狀態
        state.hotel_recommendations = response
        state.messages.append({"role": "system", "content": response})
        return state  # 回傳更新後的 State
    
# 景點agent
class TravelAdvisor(Runnable):
    def invoke(self, state: State, config=None) -> State:
        user_query = state.messages[-1].content
        prompt = f"請根據以下需求推薦旅遊地點：{user_query}"
        #response = ray.get(client.text_generation(prompt, max_new_tokens=500))
        response = ray.get(client.generate.remote(prompt))
        logger.info(f"Travel Plan Generated: {response}")

        # 更新狀態
        state.travel_plan = response
        state.messages.append({"role": "system", "content": response})
        return state  # 回傳更新後的 State
# 匯總分析agent
class AnalysisAdvisor(Runnable):
    def invoke(self, state: State, config=None) -> State:
        prompt = "請根據以下飯店及景點資訊，產生完整的旅遊分析報告：\n"
        prompt += f"飯店推薦：{state.hotel_recommendations}\n"
        prompt += f"旅遊規劃：{state.travel_plan}"
        
        response = ray.get(client.generate.remote(prompt))
        logger.info(f"Generated Analysis Report: {response}")
        
        state.analysis_report = response
        state.messages.append({"role": "system", "content": response})
        return state


builder = StateGraph(State)
builder.add_node("primary_advisor", PrimaryAdvisor())  
builder.add_node("hotel_advisor", HotelAdvisor())  
builder.add_node("travel_advisor", TravelAdvisor())  
builder.add_node("analysis_advisor", AnalysisAdvisor())  

builder.add_edge(START, "primary_advisor")  
builder.add_edge("primary_advisor", "hotel_advisor")  
builder.add_edge("primary_advisor", "travel_advisor")  
builder.add_edge("hotel_advisor", "analysis_advisor")  
builder.add_edge("travel_advisor", "analysis_advisor")  
builder.add_edge("analysis_advisor", END)

graph = builder.compile()

if __name__ == "__main__":
    user_input = "我想去台中旅遊，住兩晚，3 個大人 2 個小孩，每天預算 5000 以內"
    initial_state = State(city="台中市", messages=[{"role": "user", "content": user_input}])
    
    result = graph.invoke(initial_state)
    
    print("\n[住宿推薦]")
    print(result.hotel_recommendations if result.hotel_recommendations else "無法提供住宿資訊")
    
    print("\n[旅遊規劃]")
    print(result.travel_plan if result.travel_plan else "無法提供建議")
    
    print("\n[綜合分析報告]")
    print(result.analysis_report if result.analysis_report else "無法產生報告")

