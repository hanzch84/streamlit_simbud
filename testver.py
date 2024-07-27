import streamlit as st
import pandas as pd
import numpy as np

# 스트림릿 헤더 설정
st.markdown("""
# 편리한 예산 만들기
### SimBud beta (Budget Simulator V1.01)
by 교수 박현수, 버그 및 개선 문의: [hanzch84@gmail.com](mailto:hanzch84@gmail.com)
""")

# 예산 입력
budget = st.number_input('사용할 예산', value=300402)

# 물품 입력
item1 = st.number_input('물품1 최대구매량', value=2503)
item2 = st.number_input('물품2 최대구매량', value=69)
item3 = st.number_input('물품3 최대구매량', value=883)
item4 = st.number_input('물품4 최대구매량', value=469)
item5 = st.number_input('물품5 최대구매량', value=698)

# 구입량 리스트
purchase_amounts = [item1, item2, item3, item4, item5]

# 구입량 분산 계산
variances = np.var(purchase_amounts)

# 평균과 표준편차 계산
mean_variance = np.mean(variances)
std_deviation = np.std(variances)

# 상한선 및 하한선 설정
lower_bound = mean_variance - std_deviation
upper_bound = mean_variance + std_deviation

# 조건에 맞는 물품 선택
selected_items = [item for item in purchase_amounts if lower_bound <= np.var(item) <= upper_bound]

# 결과 출력
st.write(f'선택된 물품들: {selected_items}')

# 예산 내에서 가능한지 확인
total_cost = sum(selected_items)
if total_cost <= budget:
    st.success("선택된 물품들로 예산 내에서 구매 가능합니다.")
else:
    st.error("예산을 초과합니다. 다른 물품을 선택하세요.")

# 예제 데이터
data = {
    ("금액", ""): [253, 250, 247, 244, 242, 239, 236, 233, 230, 227],
    ("물품1", "4,330원"): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("물품2", "640원"): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("물품3", "430원"): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("물품4", "340원"): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ("물품5", "120원"): [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}

# 멀티인덱스 생성
columns = pd.MultiIndex.from_tuples(data.keys())
df = pd.DataFrame(data.values(), index=range(1, 11), columns=columns).T

# 멀티헤더 데이터프레임 출력
st.dataframe(df, use_container_width=True, hide_index=True, height=500)
