import streamlit as st
import numpy as np
import pandas as pd
import unicodedata
import time
from functools import reduce

# startupdate
st.markdown(
    """
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            function selectAllText(event) {
                event.target.select();
            }

            // 모든 입력 필드에 이벤트 리스너 추가
            let inputs = document.querySelectorAll("input, textarea");
            inputs.forEach(input => {
                input.addEventListener("focus", selectAllText);
            });
        });
    </script>
    """,
    unsafe_allow_html=True
)

# endupdate

result_text = '''예산과 단가를 입력한 후\n계산하기 버튼을 누르면,
예산에 딱 맞게 물건을\n살 수 있는 방법을 찾아줍니다.\n
데이터프레임으로 출력된 결과에
마우스를 올리면 저장도 가능해요.\n
물품 이름은 안 쓰셔도 작동합니다.
단가가 0인 품목은 자동으로 제외합니다.
물품 추가 버튼을 눌러\n물품을 추가할 수도 있고,
체크 박스의 체크 표시를 해제하면\n잠시 계산에서 제외할 수도 있습니다.
기본 구매량과 최대 구매량을 제한할 수 있습니다.
'''
# ＊스타일 구역＊ Streamlit 페이지에 CSS를 추가
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic+Coding&display=swap');
        /* 폰트와 텍스트 스타일 설정 */
        .stTextInput, .stButton > button, .stSelectbox, .stDateInput, .stTimeInput, 
        input[type="number"], code[class="language-java"], p, input[type="text"],
        textarea[aria-label="결과 출력"]{
            font-family: 'Nanum Gothic Coding', monospace !important;
            font-size: 14px;color: #FFC83D;}

        /* 텍스트 정렬 */
        input[type="number"] { text-align: right; }
        h1{ text-align: center;}        
        h3{ text-align: right; margin-right: 0;margin-top: 0;padding-top: 0;padding-right: 0;line-height: 1.2;}        

        /* 체크박스 스타일 */
        [data-testid="stCheckbox"] {
            margin-left: 5px;
            margin-right: -5px;
            height: 1rem;
            width: 1rem;}

        /* 여백과 간격 조정 */
        input[type="number"], textarea[aria-label="결과 출력"], input[type="text"], 
        [data-testid="stVerticalBlock"] > div:first-child {margin: 2px;}
        input[aria-label="budget"]{margin: 0px;font-size: 24px;font-weight: bold;}
        [data-testid="stNotificationContentWarning"]{margin: -8px;font-size: 16px;}

        /* stHorizontalBlock 요소 간의 간격 조절 */
        [data-testid="stHorizontalBlock"] {
            margin-bottom: -18px; /* 기존보다 작은 값으로 설정하여 간격 줄이기 */
            
        }
        [data-testid="column"] {
            margin-right: -4px; /* 기존보다 작은 값으로 설정하여 간격 줄이기 */
            margin-left: -4px; /* 기존보다 작은 값으로 설정하여 간격 줄이기 */
            
        }

        .stDataFrame { 
        width: 100% !important;
        }

        /* 특정 텍스트에리어의 색상 */
        h3, p { color: #FFC83D; }
        [data-testid="baseButton-secondary"],[data-testid="stDataFrameResizable"]{width: 100% !important;}
    </style>""", unsafe_allow_html=True)

# ＊함수 구역＊
# 문자열의 출력 길이를 구하는 함수(텍스트박스, 콘솔 출력용)


def get_conmplexcity(price, max, min):
    last_index = price.label(min(price))
    combination = [x-y+1 for x, y in zip(max, min)]
    combination[last_index] = 1
    return reduce(lambda x, y: x * y, combination)


def get_print_length(s):
    screen_length = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ['F', 'W']:
            screen_length += 2
        else:
            screen_length += 1
    return screen_length

# 문자열을 출력 길이에 맞게 자르는 함수(텍스트박스, 콘솔 출력용)


def cut_string(org_s, max_length, pad_LR="R"):
    cut_s, length = '', 0
    for char in org_s:
        char_length = get_print_length(char)
        if length + char_length > max_length:
            break
        cut_s += char
        length += char_length
    diff = max_length-length
    if diff > 0:
        if pad_LR == "L":
            return diff * " " + cut_s
        if pad_LR == "R":
            return cut_s + diff * " "
    else:
        return cut_s

# 아이템 활성화/비활성화 업데이트 함수(스트림릿 위젯 제어용)


def update_item_availability(i, budget):
    item_price = st.session_state.get(f"item_price_{i}", 0)
    if budget > 0 and item_price > 0 and item_price <= budget:
        max_quantity = budget // item_price
        st.session_state[f"item_max_{i}"] = max_quantity
        st.session_state[f"item_max_max_value_{i}"] = max_quantity
        st.session_state[f"item_min_min_value_{i}"] = max_quantity
        st.session_state[f"item_disabled_{i}"] = False
    else:
        st.session_state[f"item_disabled_{i}"] = True

# 예산 변경 시 호출되는 함수


def on_budget_change():
    budget = st.session_state.get("budget", 0)
    if 'item_count' in st.session_state:
        for i in range(st.session_state.item_count):
            update_item_availability(i, budget)
            on_max_change(i)

# 단가 변경 시 호출되는 함수


def on_price_change():
    budget = st.session_state.get("budget", 0)
    # 모든 아이템에 대해 update_item_availability 함수를 호출합니다.
    for i in range(st.session_state.item_count):
        update_item_availability(i, budget)

# 아이템의 최소 구매량 입력 필드가 변경될 때 호출되는 함수


def on_min_change(index, min_quantities, item_prices):
    # 현재 아이템의 최소, 최대 구매량 및 단가 가져오기
    current_min = st.session_state.get(f'item_min_{index}', 0)
    current_max = st.session_state.get(f'item_max_{index}', 0)
    current_price = st.session_state.get(f'item_price_{index}', 0)
    budget_input = st.session_state.get("budget")

    # 모든 아이템에 대해 최소 구매량과 단가를 곱한 총액 계산
    total_min_cost = sum(a * b for a, b in zip(min_quantities, item_prices))

    # 예산 초과 시 조정
    if total_min_cost > budget_input and current_price != 0:
        # 예산 초과분 계산
        over_budget = total_min_cost - budget_input

        # 현재 아이템의 구매량을 줄여서 예산을 맞추기
        reduce_by = min(current_min, (over_budget +
                        current_price - 1) // current_price)
        new_min = current_min - reduce_by
        st.session_state[f'item_min_{index}'] = new_min

    # 최소 구매량이 최대 구매량을 초과하는 경우 조정
    elif current_min > current_max:
        st.session_state[f'item_min_{index}'] = current_max


def on_max_change(index):
    current_max = st.session_state.get(f"item_max_{index}", 0)
    current_min = st.session_state.get(f'item_min_{index}', 0)
    current_price = st.session_state.get(f'item_price_{index}', 0)
    budget = st.session_state.get("budget")
    # 에러처리
    # 최대구매개수 * 단가가 예산을 넘는 경우 가능한 최대값으로 지정, 에러메시지
    if (current_price * current_max) > budget:
        st.session_state[f'item_max_{index}'] = budget//current_price
    # 위 조건을 통과한 것 중 최대구매개수가 최소구매값보다 작으면, 최소구매값과 일치.
    elif current_min > current_max:
        st.session_state[f'item_max_{index}'] = current_min

# 예산 계산 함수


def calculate_budget(budget, labels, prices, base_quantity, limited_quantity):
    """메모이제이션 + 마지막 아이템 나눗셈 처리"""
    try:
        text_out = f'사용해야 할 예산은 {format(budget,",")}원입니다.\n'
        item_count = len(prices)
        
        # 정렬
        combined = zip(prices, labels, base_quantity, limited_quantity)
        sorted_combined = sorted(combined, reverse=True)
        prices, labels, base_quantity, limited_quantity = map(list, zip(*sorted_combined))
        
        # 정렬된 데이터 출력
        text_width = 25
        text_out += '_' * text_width + '정렬된 데이터' + '_' * text_width + '\n'
        for n_prt in range(item_count):
            label = cut_string(labels[n_prt], 28)
            text_out += f"품목 #{n_prt + 1:02d} {label} = {prices[n_prt]:7,d} 원 ({base_quantity[n_prt]:3d}  ~ {limited_quantity[n_prt]:3d})\n"
        text_out += '_' * (text_width * 2 + 13) + '\n'
        
        # 전처리
        total_budget = budget
        fixed_budget = sum(a * b for a, b in zip(base_quantity, prices))
        remaining_budget = budget - fixed_budget
        limits = [lim - base for lim, base in zip(limited_quantity, base_quantity)]
        last_idx = item_count - 1
        
        time_limit = 20
        start_time = time.time()
        memo = {}
        call_count = 0
        
        # 1단계: 마지막 아이템 제외하고 해 존재 여부 계산
        def count_solutions(idx, remaining):
            nonlocal call_count
            call_count += 1
            
            if call_count % 100000 == 0:
                if time.time() - start_time > time_limit:
                    raise TimeoutError(f"시간초과: {time_limit}초 경과")
            
            if remaining < 0:
                return 0
            
            # 마지막 직전 아이템까지 왔으면, 마지막 아이템으로 나눠떨어지는지 체크
            if idx == last_idx:
                qty = remaining // prices[last_idx]
                if qty <= limits[last_idx] and remaining % prices[last_idx] == 0:
                    return 1
                return 0
            
            if (idx, remaining) in memo:
                return memo[(idx, remaining)]
            
            total = 0
            for qty in range(limits[idx] + 1):
                cost = qty * prices[idx]
                if cost > remaining:
                    break
                total += count_solutions(idx + 1, remaining - cost)
            
            memo[(idx, remaining)] = total
            return total
        
        exact_count = count_solutions(0, remaining_budget)
        
        # 2단계: 역추적
        cases_exact = []
        
        def reconstruct(idx, remaining, current):
            if time.time() - start_time > time_limit:
                raise TimeoutError(f"시간초과: {time_limit}초 경과")
            
            # 마지막 아이템: 나눗셈으로 처리
            if idx == last_idx:
                if remaining % prices[last_idx] == 0:
                    qty = remaining // prices[last_idx]
                    if qty <= limits[last_idx]:
                        cases_exact.append(current + [qty])
                return
            
            for qty in range(limits[idx] + 1):
                cost = qty * prices[idx]
                if cost > remaining:
                    break
                
                next_remaining = remaining - cost
                # 해가 존재하는 경로만 탐색
                if memo.get((idx + 1, next_remaining), 0) > 0:
                    current.append(qty)
                    reconstruct(idx + 1, next_remaining, current)
                    current.pop()
                # 마지막 직전이면 직접 체크
                elif idx + 1 == last_idx:
                    if next_remaining % prices[last_idx] == 0:
                        qty_last = next_remaining // prices[last_idx]
                        if qty_last <= limits[last_idx]:
                            cases_exact.append(current + [qty, qty_last])
        
        if exact_count > 0:
            reconstruct(0, remaining_budget, [])
        
        # 근사치 처리 (정확한 해가 없을 때)
        cases_close = []
        if exact_count == 0:
            best_remaining = remaining_budget
            
            def find_closest(idx, remaining, current):
                nonlocal best_remaining
                if time.time() - start_time > time_limit:
                    return
                
                if idx == last_idx:
                    qty = min(remaining // prices[last_idx], limits[last_idx])
                    leftover = remaining - qty * prices[last_idx]
                    if leftover < best_remaining:
                        best_remaining = leftover
                        cases_close.clear()
                        cases_close.append(current + [qty])
                    elif leftover == best_remaining:
                        cases_close.append(current + [qty])
                    return
                
                for qty in range(limits[idx] + 1):
                    cost = qty * prices[idx]
                    if cost > remaining:
                        break
                    current.append(qty)
                    find_closest(idx + 1, remaining - cost, current)
                    current.pop()
            
            find_closest(0, remaining_budget, [])
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"실행 시간: {execution_time:.4f}초, 메모 상태 수: {len(memo):,}")
        
        # 결과 출력
        if exact_count == 0:
            text_out += f'{total_budget:,d}원의 예산에 맞게 구입할 방법이 없습니다.\n'
            text_out += '예산에 근접한 구입 계획은 아래와 같습니다.\n'
            list_show = cases_close
        else:
            text_out += f'예산에 맞는 {len(cases_exact):,d}개의 완벽한 방법을 찾았습니다.\n'
            list_show = cases_exact
        
        list_show = (np.array(list_show) + np.array(base_quantity)).tolist() if list_show else []
        text_out += f'이 프로그램은 {call_count:,d}개의 상태를 계산했습니다.\n'
        
        return text_out, list_show, prices
    
    except TimeoutError as e:
        return f'에러입니다.: {e}', [], prices
    except Exception as e:
        print('Error Message:', e)
        return f'에러입니다.: {e}', [], prices

# 웹 앱 UI 구현
result_list, result_prices = [], []

st.title("편리한 예산🍞만들기")
st.markdown('<p style="color: #a8a888;text-align: right;">SimBud beta (Budget Simulator V1.00)by 교사 박현수, 버그 및 개선 문의: <a href="mailto:hanzch84@gmail.com">hanzch84@gmail.com</a></p>', unsafe_allow_html=True)

col_label_budget, col_input_budget = st.columns([3, 7])
with col_label_budget:
    st.subheader("사용할 예산")
with col_input_budget:
    # 예산 입력란
    budget_input = st.number_input("budget", min_value=0, key="budget", help="사용해야하는 예산을 입력하세요.",
                                   on_change=on_budget_change, format="%d", label_visibility='collapsed')

# session_state를 확인하여 물품 개수를 관리합니다.
if 'item_count' not in st.session_state:
    st.session_state.item_count = 5

# 아이템 섹션 생성 반복문
item_names = []
item_prices = []
min_quantities = []
max_quantities = []
hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3.5, 1.4, 1.4, 3, 0.7])
with hcol1:
    st.write("물품이름")
with hcol2:
    st.write("최소구매")
with hcol3:
    st.write("최대구매")
with hcol4:
    st.write("물품단가")
with hcol5:
    st.write("선택")

for i in range(st.session_state.item_count):
    col1, col2, col3, col4, col5 = st.columns([3.5, 1.4, 1.4, 3, 0.7])
    # 체크박스가 해제되어 있는지 체크해 입력 필드들을 비활성화를 결정합니다.
    is_disabled = not st.session_state.get(f'item_usable_{i}', True)
    with col1:
        item_name = st.text_input(f"물품{i+1} 이름 입력", label_visibility='collapsed',
                                  key=f"item_name_{i}", placeholder=f"물품{i+1} 이름 입력",
                                  disabled=is_disabled)
    with col2:
        item_min = st.number_input(f"최소 {i+1}",
                                   on_change=on_min_change(
                                       i, min_quantities, item_prices),
                                   min_value=0,
                                   max_value=st.session_state.get(
                                       f'item_min_max_value_{i}',),
                                   key=f"item_min_{i}",
                                   # 여기에 disabled 상태를 적용합니다.
                                   disabled=is_disabled or st.session_state.get(
                                       f"item_disabled_{i}", True),
                                   format="%d", label_visibility='collapsed')
    with col3:
        item_max = st.number_input(f"최대 {i+1}",
                                   on_change=on_max_change(i),
                                   min_value=st.session_state.get(
                                       f'item_max_min_value_{i}', 0),
                                   key=f"item_max_{i}",
                                   # 여기에 disabled 상태를 적용합니다.
                                   disabled=is_disabled or st.session_state.get(
                                       f"item_disabled_{i}", True),
                                   format="%d", label_visibility='collapsed')
    with col4:
        item_price = st.number_input(f"물품단가{i+1}",
                                     min_value=0,
                                     key=f"item_price_{i}",
                                     value=0,
                                     # 여기에 이벤트 핸들러를 연결합니다.
                                     on_change=on_price_change,
                                     disabled=is_disabled, format="%d", label_visibility='collapsed')
    with col5:
        # 체크박스를 만들고 session state value를 만듭니다.
        item_usable = st.checkbox(f'물품{i+1}', label_visibility='collapsed',
                                  key=f'item_usable_{i}',
                                  value=st.session_state.get(f'item_usable_{i}', True))
        st.write("")

    # 체크박스에 체크가 되어 있고 가격이 0보다 크면 리스트에 다음을 추가합니다.(이름,가격,최소,최대)
    if item_usable and item_price > 0:
        item_names.append(item_name if item_name else '')
        item_prices.append(item_price)
        min_quantities.append(item_min)
        max_quantities.append(item_max)

col_left, col_label_fixed, col_right = st.columns([2, 9, 2])

# 물품추가 버튼 클릭 시 호출되는 함수


def add_item():
    st.session_state.item_count += 1


# 물품추가 버튼에 콜백 함수 연결
with col_left:
    if st.button("물품추가", on_click=add_item):
        pass

with col_label_fixed:
    fixed_budget = sum(a * b for a, b in zip(min_quantities, item_prices))
    max_limit = sum(a * b for a, b in zip(max_quantities, item_prices))
    st.warning(
        f"확정: {fixed_budget:,d}원(남은 예산: {(budget_input - fixed_budget):,d}원) 구매제한: {max_limit:,d}원")

# 계산 버튼 클릭 이벤트 핸들러
with col_right:
    if st.button("계산하기"):
        if budget_input != st.session_state.get("budget", 0):
            on_budget_change()
        if budget_input == "" or budget_input <= 0:
            result_text = '예산을 정확히 입력하세요.(*0보다 큰 자연수)'
        elif len(item_prices) <= 1:
            result_text = '최소 2종류 이상의 단가를 입력하세요.'
        elif min(item_prices) <= 0:
            result_text = '단가가 0보다 작거나 같습니다.'
        elif max(item_prices) > budget_input:
            result_text = '예산이 부족합니다.'
        elif max_limit < budget_input:
            result_text = f'최대구매금액({max_limit:,d}원)이 예산({budget_input:,d}원)보다 작아 예산을 다 쓸 수 없습니다.'
        elif fixed_budget > budget_input:
            result_text = f'최소구매금액({fixed_budget:,d}원)이 예산({budget_input:,d}원)보다 많아 예산 내에서 쓸 수 없습니다.'
        elif len(item_prices) != len(set(item_prices)):
            result_text = '중복된 단가가 있습니다.'
        else:
            # 스피너를 표시하면서 계산 진행 오버레이와 스피너를 위한 컨테이너 생성
            overlay_container = st.empty()
            # 오버레이와 스피너 추가
            overlay_container.markdown("""
            <style>
            .overlay {
                position: fixed;top: 0;left: 0;width: 100%;height: 100%;
                background: rgba(0, 0, 0, 0.5);z-index: 999;display: flex;
                justify-content: center;align-items: center;                }
            .spinner {margin-bottom: 10px;}
            </style>
            <div class="overlay"><div><div class="spinner">
                        <span class="fa fa-spinner fa-spin fa-3x"></span>
                    </div><div style="color: white;">계산 중...</div></div></div>""", unsafe_allow_html=True)

            # 계산 결과를 구합니다.
            result_text, result_list, result_prices = calculate_budget(
                budget_input, item_names, item_prices, min_quantities, max_quantities)
            # 작업이 완료되면 오버레이와 스피너를 제거합니다.
            overlay_container.empty()
if len(result_text.split('\n')) < 30:
    st.code(result_text, language="java")
else:
    st.text_area("결과 출력", result_text, height=300)

try:
    df = pd.DataFrame(result_list, columns=[
                      f'{price:,d}원' for price in result_prices])
    # 새로운 열 '금액'을 계산하고 데이터프레임에 추가합니다.
    df['금액'] = df.mul(result_prices).sum(axis=1)
    if df.__len__() != 0:
        # 결과를 화면에 표시합니다.
        st.dataframe(df, hide_index=True, use_container_width=True)
except:
    pass
