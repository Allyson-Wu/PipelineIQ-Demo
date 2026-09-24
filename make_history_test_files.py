import pandas as pd
import numpy as np
import os

# 確保 test_files 資料夾存在
os.makedirs("test_files", exist_ok=True)

# 基礎乾淨資料集範本 (模擬 100 筆交易紀錄)
np.random.seed(42)
n_rows = 100

base_data = {
    "transaction_id": [f"TXN_{1000 + i}" for i in range(n_rows)],
    "customer_id": [f"CUST_{np.random.randint(100, 200)}" for _ in range(n_rows)],
    "amount": np.round(np.random.uniform(10.0, 500.0, n_rows), 2),
    "category": np.random.choice(["Electronics", "Clothing", "Food", "Books"], n_rows),
    "status": np.random.choice(["COMPLETED", "PENDING", "FAILED"], n_rows)
}

# 1. 產生 Jan 檔案 (良好，約 95 分)
df_jan = pd.DataFrame(base_data).copy()
df_jan.loc[0:4, "amount"] = np.nan  # 5% 缺失
df_jan.to_csv("test_files/test_q1_jan.csv", index=False)

# 2. 產生 Feb 檔案 (品質下滑，約 75 分)
df_feb = pd.DataFrame(base_data).copy()
df_feb.loc[0:15, "amount"] = np.nan  # 16% 缺失
df_feb.loc[10:20, "category"] = np.nan  # 11% 缺失
df_feb.to_csv("test_files/test_q1_feb.csv", index=False)

# 3. 產生 Mar 檔案 (品質嚴重受損，約 55 分)
df_mar = pd.DataFrame(base_data).copy()
df_mar.loc[0:30, "amount"] = np.nan
df_mar.loc[20:50, "category"] = np.nan
df_mar.loc[40:60, "status"] = np.nan
# 加入 5 筆重複列
df_mar = pd.concat([df_mar, df_mar.iloc[0:5]], ignore_index=True)
df_mar.to_csv("test_files/test_q1_mar.csv", index=False)

# 4. 產生 Apr 檔案 (品質回升，約 88 分)
df_apr = pd.DataFrame(base_data).copy()
df_apr.loc[0:8, "amount"] = np.nan
df_apr.to_csv("test_files/test_q1_apr.csv", index=False)

# 5. 產生 May 檔案 (完美資料，100 分)
df_may = pd.DataFrame(base_data).copy()
df_may.to_csv("test_files/test_q1_may.csv", index=False)

print("✅ 成功產生 5 個歷史測試檔案於 test_files/ 目錄下：")
print("1. test_q1_jan.csv")
print("2. test_q1_feb.csv")
print("3. test_q1_mar.csv")
print("4. test_q1_apr.csv")
print("5. test_q1_may.csv")