import os, json, re
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title='TPOWI 2.0 | 냉장고를 부탁해',page_icon='🥑',layout='centered')
st.markdown('''<style>@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');.stApp{background:#f8faf6;color:#203a33}.block-container{max-width:850px;padding-top:2rem}h1,h2,h3{color:#20483a!important}.hero{background:linear-gradient(115deg,#d7f2df,#fef5dc);border-radius:24px;padding:30px;margin-bottom:20px}.eyebrow{letter-spacing:3px;color:#648776;font-weight:700}.tag{display:inline-block;background:#e6f3e8;color:#31634c;border-radius:30px;padding:5px 12px;margin:3px;font-size:13px}.recipe{background:white;border:1px solid #e2ece4;border-radius:20px;padding:20px;margin:10px 0}.small{color:#617c70;font-size:14px}div.stButton>button[kind="primary"]{background:#2f7655;border-radius:12px;border:0}div.stButton>button{border-radius:12px}</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">YOUR SMART KITCHEN COMPANION</div><h1>🥑 TPOWI 2.0</h1><h3>냉장고를 부탁해</h3><p>내 냉장고 속 재료와 오늘의 상황을 조합해, 딱 맞는 한 끼를 찾아요.</p><span class="tag">재료 중심 추천</span><span class="tag">TPOW 맞춤 조건</span><span class="tag">Gemini AI</span></div>',unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results=[]
if 'excluded' not in st.session_state: st.session_state.excluded=[]
if 'selected' not in st.session_state: st.session_state.selected=None
if 'saved' not in st.session_state: st.session_state.saved=[]

with st.sidebar:
    st.header('⚙️ AI 연결')
    key=os.getenv('GEMINI_API_KEY','')
    try: key=st.secrets.get('GEMINI_API_KEY',key)
    except Exception: pass
    if not key: key=st.text_input('Gemini API 키',type='password',help='입력한 키는 이 세션에서만 사용합니다.')
    model=st.text_input('모델 이름',value='gemini-3.8-flash',help='계정에서 사용 가능한 모델명으로 변경할 수 있습니다.')
    st.caption('API 키를 코드나 공개 저장소에 올리지 마세요. 입력 조건은 Gemini API로 전송됩니다.')
    st.divider()
    st.caption('2022 TPOWI 아이디어를 바탕으로 새로 구현한 2.0 프로토타입')

st.subheader('01  🧺 냉장고 속 재료')
items=st.text_input('지금 가지고 있는 재료를 쉼표로 구분해 입력하세요',value='달걀, 감자, 양파, 두부',placeholder='예: 달걀, 양파, 감자')
owned=[x.strip() for x in re.split('[,，\n]',items) if x.strip()]
if owned: st.markdown(''.join(f'<span class="tag">{x.replace("<","&lt;").replace(">","&gt;")}</span>' for x in owned),unsafe_allow_html=True)

st.subheader('02  ☀️ 오늘의 TPOW')
a,b=st.columns(2)
with a:
    when=st.selectbox('⏰ 시간', ['점심','저녁','아침','간식','야식'])
    place=st.selectbox('📍 장소',['집','회사·학교','야외·피크닉','기타'])
    minutes=st.slider('⏳ 최대 조리 시간 (분)',10,90,30,5)
with b:
    occasion=st.selectbox('🍽️ 상황',['혼자 간단히','가족 식사','손님 초대','도시락','든든한 한 끼'])
    weather=st.selectbox('🌤️ 날씨',['상관없음','맑음','비','추움','더움'])
    servings=st.number_input('인분',1,8,1)

st.subheader('03  🌱 취향과 식재료 제한')
likes=st.text_input('선호하는 음식이나 맛 (선택)',placeholder='예: 매콤한 한식, 국물 요리')
dislikes=st.text_input('피하고 싶은 재료 (선택)',placeholder='예: 버섯, 고수')
allergies=st.multiselect('알레르기 유발 식재료 (선택)', ['달걀','우유','땅콩','대두','밀','메밀','새우','게','조개류','생선','견과류','참깨','복숭아','토마토','기타'])
other_allergy=st.text_input('기타 알레르기 (선택)',placeholder='직접 입력') if '기타' in allergies else ''
with st.expander('건강 관련 참고 조건 (선택 · 민감정보 입력 주의)'):
    st.caption('건강정보는 입력하지 않아도 됩니다. 이 데모는 질환별 식이 안전성을 검증하지 않습니다. 의료 목적에 사용하지 마세요.')
    notes=st.text_input('일반적인 식사 선호만 입력 권장',placeholder='예: 싱겁게 먹기')

restricted=[x for x in allergies if x!='기타']+([other_allergy] if other_allergy else [])

def create_recipes(excluded):
    payload={'owned_ingredients':owned,'meal':when,'place':place,'occasion':occasion,'weather':weather,'max_minutes':minutes,'servings':servings,'likes':likes,'dislikes':dislikes,'allergies':restricted,'other_preferences':notes,'exclude_previous':excluded}
    system='''너는 한국어 레시피 추천 엔진이다. JSON만 출력한다. 제공된 보유 재료를 최대한 사용하고 최대 조리시간을 지켜라. 알레르기 성분과 피하는 재료는 절대 포함하지 마라. 단, 알레르기 교차접촉, 제품 성분, 실제 안전성은 확인할 수 없으므로 결과는 검토가 필요하다. 입력된 건강 선호를 의료적 판단으로 확대하지 마라. 메뉴 3개를 서로 다르게 추천하라. 필수 양념도 재료 목록에 포함한다. 재료 표기는 짧고 일관된 한국어 명사로 작성한다. 레시피 각 단계는 1문장으로 간결하게. 응답 형식: {"recipes":[{"name":"...","emoji":"🍳","description":"...","reason":"...","minutes":20,"ingredients":["달걀","양파"],"steps":["..."],"tip":"..."}]}'''
    with genai.Client(api_key=key) as client:
        response=client.models.generate_content(model=model,contents=json.dumps(payload,ensure_ascii=False),config=types.GenerateContentConfig(system_instruction=system,response_mime_type='application/json',temperature=0.65))
    data=json.loads(response.text)
    if not isinstance(data.get('recipes'),list) or not data['recipes']: raise ValueError('추천 결과 형식이 올바르지 않습니다.')
    clean=[]
    for r in data['recipes'][:3]:
        ingredients=[str(x).strip() for x in r.get('ingredients',[]) if str(x).strip()]
        if not ingredients: continue
        # 보수적 텍스트 검사: 정확한 알레르기 안전성 검증을 보장하지 않음
        content=' '.join([r.get('name',''),r.get('description','')]+ingredients+r.get('steps',[]))
        if any(a.lower() in content.lower() for a in restricted+([x.strip() for x in dislikes.split(',') if x.strip()])): continue
        r['ingredients']=ingredients
        r['have']=[x for x in ingredients if any(x.replace(' ','')==y.replace(' ','') for y in owned)]
        r['missing']=[x for x in ingredients if x not in r['have']]
        clean.append(r)
    if not clean: raise ValueError('제한 재료를 제외하니 표시할 메뉴가 없습니다. 조건을 변경해 주세요.')
    return clean

if st.button('✨ 오늘의 메뉴 3개 추천받기',type='primary',use_container_width=True):
    if not owned: st.warning('냉장고 재료를 하나 이상 입력해 주세요.')
    elif not key: st.warning('왼쪽 사이드바에서 Gemini API 키를 입력해 주세요.')
    else:
        with st.spinner('냉장고 속 재료와 오늘의 상황을 조합하고 있어요...'):
            try:
                st.session_state.results=create_recipes(st.session_state.excluded)
                st.session_state.selected=None
            except Exception as e: st.error(f'추천 생성 실패: {e}')

if st.session_state.results:
    st.subheader('04  🍴 오늘의 추천 메뉴')
    for idx,r in enumerate(st.session_state.results):
        with st.container(border=True):
            st.markdown(f'### {r.get("emoji","🍽️")} {r.get("name","추천 메뉴")}')
            st.write(r.get('description',''))
            st.caption(f'⏱ 약 {r.get("minutes","?")}분 · {servings}인분')
            st.info('💡 추천 이유: '+r.get('reason',''))
            c1,c2=st.columns(2)
            with c1: st.markdown('**🟢 보유 재료**');st.write(', '.join(r['have']) or '없음')
            with c2: st.markdown('**🛒 부족한 재료**');st.write(', '.join(r['missing']) or '없음')
            if st.button('레시피 자세히 보기',key=f'view_{idx}'):
                st.session_state.selected=idx
            if st.session_state.selected==idx:
                st.markdown('#### 만드는 방법')
                for n,step in enumerate(r.get('steps',[]),1): st.write(f'{n}. {step}')
                if r.get('tip'):st.caption('👩‍🍳 '+r['tip'])
                st.warning('⚠️ AI 생성 레시피입니다. 알레르기·식품 안전·조리 상태를 직접 확인하세요. 교차접촉 가능성도 점검하세요.')
            if st.button('💚 이 메뉴 저장',key=f'save_{idx}'):
                if r['name'] not in [s['name'] for s in st.session_state.saved]: st.session_state.saved.append(r)
                st.toast('이 세션의 찜 목록에 저장했어요!')
    if st.button('🔄 다른 메뉴 다시 추천',use_container_width=True):
        if not key: st.warning('API 키가 필요합니다.')
        else:
            st.session_state.excluded.extend(r['name'] for r in st.session_state.results)
            with st.spinner('다른 메뉴를 찾는 중...'):
                try: st.session_state.results=create_recipes(st.session_state.excluded);st.session_state.selected=None;st.rerun()
                except Exception as e: st.error(f'다시 추천 실패: {e}')

if st.session_state.saved:
    with st.expander(f'📖 저장한 메뉴 ({len(st.session_state.saved)})'):
        for r in st.session_state.saved: st.write('• '+r['name'])
        st.download_button('저장한 레시피 JSON 내보내기',data=json.dumps(st.session_state.saved,ensure_ascii=False,indent=2),file_name='tpowi_recipes.json',mime='application/json')
st.divider()
st.caption('TPOWI 2.0 · 2022 TPOWI 스마트 냉장고 프로젝트 고도화 · 개인 학습/포트폴리오용 프로토타입')
