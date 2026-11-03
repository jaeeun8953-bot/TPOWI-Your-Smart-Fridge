import os, json, re, urllib.parse, urllib.request
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title='TPOWI 2.0 | 냉장고를 부탁해',page_icon='🥑',layout='centered')
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Noto+Sans+KR:wght@400;500;600;700;800;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Nunito','Noto Sans KR',sans-serif}
.stApp{background:radial-gradient(circle at 95% 5%,rgba(255,198,116,.29),transparent 34%),radial-gradient(circle at 4% 32%,rgba(148,221,183,.24),transparent 36%),linear-gradient(145deg,#fff9f0 0%,#fffdf8 52%,#f0fbf4 100%);color:#283e36}
.block-container{max-width:780px!important;padding-top:2.3rem!important;padding-bottom:4rem!important}
h1,h2,h3,h4{color:#24493b!important;letter-spacing:-.035em!important}
h1{font-weight:900!important;font-size:clamp(2.3rem,5vw,3.5rem)!important;line-height:1.23!important}
h2,h3{font-weight:800!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#fef6e8,#f2faf1)}
[data-testid="stSidebar"]>div:first-child{border-right:1px solid #f2e5d3}
[data-testid="stCaptionContainer"]{color:#73877d}
[data-testid="stProgress"]>div>div>div{background:linear-gradient(90deg,#ff8d6a,#ffbc59,#6ac9a0)!important}
.stButton>button{border-radius:15px!important;border:1px solid #e8ded0!important;background:#fffdf9!important;color:#365c4b!important;font-weight:800!important;min-height:48px;box-shadow:0 4px 12px rgba(74,72,44,.05);transition:transform .12s,box-shadow .12s}
.stButton>button:hover{border-color:#ff9d79!important;box-shadow:0 7px 20px rgba(244,127,83,.14);transform:translateY(-1px)}
.stButton>button[kind="primary"]{background:linear-gradient(105deg,#ff805e,#ffae67)!important;color:#fff!important;border:0!important;box-shadow:0 7px 18px rgba(255,128,94,.23)!important}
[data-testid="stForm"]{background:rgba(255,255,255,.82);border:1px solid #f0e5d5;border-radius:26px;padding:24px;box-shadow:0 15px 35px rgba(111,88,53,.06)}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{border-radius:12px!important}
[data-testid="stAlert"]{border-radius:15px!important}
.brandbar{display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.82);border:1px solid #f0e6d9;border-radius:18px;padding:13px 18px;margin-bottom:30px;box-shadow:0 5px 18px rgba(91,70,43,.04)}
.brandname{font-size:17px;font-weight:900;letter-spacing:.03em;color:#2e604a}.brandpill{background:#e4f7eb;color:#378665;padding:6px 12px;border-radius:99px;font-size:11px;font-weight:800;letter-spacing:.07em}
.progresslabel{display:inline-block;background:#ffe9d7;color:#bb6843;padding:9px 14px;border-radius:100px;font-size:12px;letter-spacing:1px;font-weight:900;margin-bottom:12px}
.navcard{padding:24px 27px;border-radius:25px;background:rgba(255,255,255,.92);border:1px solid #efe7d9;margin:17px 0;box-shadow:0 13px 32px rgba(90,83,56,.065)}
.steptext{font-size:18px;line-height:1.95;white-space:pre-wrap;color:#344b42}
.photo-frame{background:#fff;border:1px solid #f0e7db;border-radius:24px;padding:12px;margin:12px auto 5px;max-width:480px;box-shadow:0 12px 28px rgba(72,70,49,.09)}
.photo-frame img{border-radius:16px!important;object-fit:cover!important;max-height:285px!important;width:100%!important}
.photo-caption{text-align:center;font-size:12px;color:#87958a;margin-top:8px}
.hero-note{background:linear-gradient(105deg,#fff1d8,#ffe7dd);border:1px solid #ffe1c8;padding:18px 20px;border-radius:20px;color:#87563d;margin:12px 0 20px;font-weight:700}
.recipe-step{background:linear-gradient(125deg,#ffffff,#fff8ef);border:1px solid #f3e6d7;border-radius:24px;padding:25px;margin:16px 0 20px;box-shadow:0 8px 25px rgba(100,75,49,.05)}
.mini-label{font-size:12px;color:#f18b62;font-weight:900;letter-spacing:1.5px;margin-bottom:10px}
.footer-note{font-size:12px;color:#87958a;text-align:center;padding:18px 0}
@media(max-width:640px){.block-container{padding-top:1.3rem!important}.navcard{padding:18px}.brandbar{margin-bottom:20px}.photo-frame{max-width:100%}}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="brandbar"><span class="brandname">🥑 TPOWI <span style="color:#f58a67">2.0</span></span><span class="brandpill">YOUR SMART FRIDGE</span></div>',unsafe_allow_html=True)


if 'results' not in st.session_state: st.session_state.results=[]
if 'excluded' not in st.session_state: st.session_state.excluded=[]
if 'selected' not in st.session_state: st.session_state.selected=None
if 'saved' not in st.session_state: st.session_state.saved=[]
if 'recipe_details' not in st.session_state: st.session_state.recipe_details={}

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


if 'page' not in st.session_state: st.session_state.page='setup'
if 'form_data' not in st.session_state: st.session_state.form_data={}
if 'recipe_index' not in st.session_state: st.session_state.recipe_index=0
if 'step_index' not in st.session_state: st.session_state.step_index=0
if 'selected_recipe' not in st.session_state: st.session_state.selected_recipe=0

def go(page):
    st.session_state.page=page
    st.session_state.scroll_to_top=True
    st.rerun()

def reset_scroll_if_needed():
    if st.session_state.pop('scroll_to_top', False):
        # Streamlit 내부 스크롤 컨테이너와 브라우저 스크롤 모두 초기화.
        # 배포 환경에서 iframe 접근이 제한되면 안전하게 무시합니다.
        import streamlit.components.v1 as components
        components.html("""<script>
        try {
          const doc = window.parent.document;
          const nodes = [doc.querySelector('[data-testid="stAppViewContainer"]'),
                         doc.querySelector('[data-testid="stMain"]'),
                         doc.querySelector('section.main'), doc.scrollingElement];
          nodes.forEach(el => {if(el){el.scrollTop=0;el.scrollTo?.({top:0,behavior:'instant'});}});
          window.parent.scrollTo({top:0,behavior:'instant'});
        } catch(e) { /* 브라우저 보안 정책상 접근 불가한 경우 */ }
        </script>""",height=0)

def step_nav(total):
    left,mid,right=st.columns([1,2,1])
    with left:
        if st.button('← 이전 단계',disabled=st.session_state.step_index<=0,use_container_width=True):
            st.session_state.step_index-=1;st.session_state.scroll_to_top=True;st.rerun()
    with mid: st.markdown(f'<p style="text-align:center;font-weight:700">{st.session_state.step_index+1} / {total}</p>',unsafe_allow_html=True)
    with right:
        if st.button('다음 단계 →',disabled=st.session_state.step_index>=total-1,use_container_width=True):
            st.session_state.step_index+=1;st.session_state.scroll_to_top=True;st.rerun()

reset_scroll_if_needed()

if st.session_state.page=='setup':
    st.markdown('<div class="progresslabel">STEP 01 / 03 · 내 냉장고</div>',unsafe_allow_html=True)
    st.title('오늘은 뭘 먹을까요?')
    st.markdown('<div class="hero-note">🍊 냉장고 속 재료가 오늘의 맛있는 한 끼가 되는 순간!<br>상황에 맞는 메뉴를 AI가 골라드려요.</div>',unsafe_allow_html=True)
    d=st.session_state.form_data
    with st.form('recipe_setup'):
        items=st.text_input('🧺 냉장고 속 재료 (쉼표로 구분)',value=d.get('items','달걀, 감자, 양파, 두부'))
        a,b=st.columns(2)
        with a:
            when=st.selectbox('⏰ 시간',['점심','저녁','아침','간식','야식'],index=['점심','저녁','아침','간식','야식'].index(d.get('when','점심')))
            place=st.selectbox('📍 장소',['집','회사·학교','야외·피크닉','기타'])
            minutes=st.slider('⏳ 최대 조리 시간',10,90,d.get('minutes',30),5)
        with b:
            occasion=st.selectbox('🍽️ 상황',['혼자 간단히','가족 식사','손님 초대','도시락','든든한 한 끼'])
            weather=st.selectbox('🌤️ 날씨',['상관없음','맑음','비','추움','더움'])
            servings=st.number_input('인분',1,8,d.get('servings',1))
        likes=st.text_input('좋아하는 맛 (선택)',value=d.get('likes',''))
        dislikes=st.text_input('피하고 싶은 재료 (선택)',value=d.get('dislikes',''))
        allergies=st.multiselect('알레르기 유발 식재료 (선택)',['달걀','우유','땅콩','대두','밀','메밀','새우','게','조개류','생선','견과류','참깨','복숭아','토마토','기타'],default=d.get('allergies',[]))
        other_allergy=st.text_input('기타 알레르기 (선택)',value=d.get('other_allergy',''))
        notes=st.text_input('식사 선호 (선택 · 건강정보 입력 주의)',value=d.get('notes',''),placeholder='예: 싱겁게 먹기')
        submitted=st.form_submit_button('✨ AI 메뉴 추천받기 →',type='primary',use_container_width=True)
    if submitted:
        if not items.strip(): st.warning('재료를 입력해 주세요.')
        elif not key: st.warning('사이드바에서 Gemini API 키를 설정해 주세요.')
        else:
            st.session_state.form_data=dict(items=items,when=when,place=place,minutes=minutes,occasion=occasion,weather=weather,servings=servings,likes=likes,dislikes=dislikes,allergies=allergies,other_allergy=other_allergy,notes=notes)
            st.session_state.excluded=[]
            st.session_state.page='loading'
            st.session_state.scroll_to_top=True
            st.rerun()

# 추천 생성과 상세 레시피 함수에서 사용하는 조건을 저장된 폼 데이터에서 복원
v=st.session_state.form_data
owned=[x.strip() for x in re.split('[,，\n]',v.get('items','')) if x.strip()]
when=v.get('when','점심');place=v.get('place','집');minutes=v.get('minutes',30)
occasion=v.get('occasion','혼자 간단히');weather=v.get('weather','상관없음');servings=v.get('servings',1)
likes=v.get('likes','');dislikes=v.get('dislikes','');notes=v.get('notes','')
restricted=[x for x in v.get('allergies',[]) if x!='기타']+([v.get('other_allergy')] if v.get('other_allergy') else [])
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


@st.cache_data(ttl=86400, show_spinner=False)
def find_food_photo(search_term):
    """Wikimedia Commons의 공개 이미지 검색. 정확한 요리 사진이라는 보장은 없음."""
    term = (search_term or '').strip()[:80]
    if not term:
        return None
    params = urllib.parse.urlencode({
        'action':'query','generator':'search','gsrsearch':f'filetype:bitmap {term} food',
        'gsrnamespace':6,'gsrlimit':8,'prop':'imageinfo','iiprop':'url|mime',
        'iiurlwidth':900,'format':'json'
    })
    req = urllib.request.Request(
        'https://commons.wikimedia.org/w/api.php?' + params,
        headers={'User-Agent':'TPOWIRecipePortfolioDemo/2.0 (educational recipe viewer)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            data=json.load(response)
        for item in data.get('query',{}).get('pages',{}).values():
            info=item.get('imageinfo',[{}])[0]
            if info.get('mime') in ('image/jpeg','image/png','image/webp'):
                return {'url':info.get('thumburl') or info.get('url'),
                        'page':info.get('descriptionurl')}
    except Exception:
        pass
    return None

def create_recipe_detail(recipe):
    instruction = """너는 요리 과정을 상세하게 설명하는 한국어 요리 도우미다.
제공된 레시피의 이름과 재료를 유지하고, 사용자가 따라할 수 있게 구체적으로 작성하라.
JSON 객체만 출력: {"summary":"요리 소개 2문장",
"ingredients_detail":[{"name":"재료명","amount":"1인분 기준 계량"}],
"preparation":["재료 손질과 사전 준비 2~4개"],
"steps_detail":[{"title":"짧은 단계 제목","instruction":"실제 조리 동작, 불 세기, 시간, 상태 확인 방법을 포함한 2~3문장","minutes":3}],
"plating":"담는 방법","storage":"보관 안내","tips":["실패 방지 팁 2~3개"],
"photo_search_term":"요리 사진 검색용 간결한 영어 요리명"}.
조리 단계는 4~7개, 전체 조리 시간은 원래 추천 시간에 가깝게 한다.
안전하지 않은 조리법은 피하고, 충분히 익혀야 하는 재료는 완전히 익히도록 안내한다.
알레르기 안전을 보증하지 말고, 없는 재료를 몰래 추가하지 마라."""
    payload={'recipe':recipe,'servings':servings,'owned_ingredients':owned,
             'allergies':restricted,'avoid_ingredients':dislikes}
    with genai.Client(api_key=key) as client:
        response=client.models.generate_content(
            model=model, contents=json.dumps(payload,ensure_ascii=False),
            config=types.GenerateContentConfig(
                system_instruction=instruction,
                response_mime_type='application/json',temperature=0.35))
    return json.loads(response.text)


if st.session_state.page=='loading':
    st.markdown('<div class="progresslabel">STEP 02 / 03 · AI 추천</div>',unsafe_allow_html=True)
    with st.spinner('오늘의 메뉴를 준비하고 있어요...'):
        try:
            st.session_state.results=create_recipes(st.session_state.excluded)
            st.session_state.recipe_index=0
            st.session_state.page='recommendations'
            st.session_state.scroll_to_top=True
            st.rerun()
        except Exception as e:
            st.error(f'메뉴 추천에 실패했어요: {e}')
            if st.button('조건 수정하기'):go('setup')

if st.session_state.page=='recommendations':
    recipes=st.session_state.results
    if not recipes: go('setup')
    idx=min(st.session_state.recipe_index,len(recipes)-1)
    r=recipes[idx]
    st.markdown('<div class="progresslabel">STEP 02 / 03 · 오늘의 추천 메뉴</div>',unsafe_allow_html=True)
    st.title('이 메뉴는 어때요?')
    st.markdown(f'<div class="hero-note">✨ 추천 메뉴 {idx+1} / {len(recipes)} · 마음에 드는 메뉴를 골라보세요</div>',unsafe_allow_html=True)
    st.markdown('<div class="navcard">',unsafe_allow_html=True)
    st.markdown(f'## {r.get("emoji","🍽️")} {r.get("name","추천 메뉴")}')
    st.write(r.get('description',''))
    st.caption(f'⏱ 약 {r.get("minutes","?")}분 · {servings}인분')
    st.info('💡 '+r.get('reason',''))
    c1,c2=st.columns(2)
    with c1: st.markdown('**🟢 보유 재료**');st.write(', '.join(r.get('have',[])) or '없음')
    with c2: st.markdown('**🛒 부족한 재료**');st.write(', '.join(r.get('missing',[])) or '없음')
    st.markdown('</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button('← 이전 메뉴',disabled=idx==0,use_container_width=True):
            st.session_state.recipe_index-=1;st.session_state.scroll_to_top=True;st.rerun()
    with c2:
        if st.button('다음 메뉴 →',disabled=idx>=len(recipes)-1,use_container_width=True):
            st.session_state.recipe_index+=1;st.session_state.scroll_to_top=True;st.rerun()
    if st.button('🍳 이 메뉴의 레시피 자세히 보기',type='primary',use_container_width=True):
        st.session_state.selected_recipe=idx
        st.session_state.step_index=0
        go('detail_loading')
    if st.button('🔄 새로운 메뉴 3개 추천받기',use_container_width=True):
        st.session_state.excluded.extend(x.get('name','') for x in recipes)
        go('loading')
    if st.button('⚙️ 조건 다시 설정',use_container_width=True):go('setup')

if st.session_state.page=='detail_loading':
    idx=st.session_state.selected_recipe
    r=st.session_state.results[idx]
    recipe_id=json.dumps({'name':r.get('name'),'ingredients':r.get('ingredients'),'steps':r.get('steps')},ensure_ascii=False,sort_keys=True)
    st.session_state.current_recipe_id=recipe_id
    if recipe_id not in st.session_state.recipe_details:
        with st.spinner('상세 조리법을 만드는 중이에요...'):
            try:
                st.session_state.recipe_details[recipe_id]=create_recipe_detail(r)
            except Exception as e:
                st.error(f'상세 조리법을 생성하지 못했어요: {e}')
                if st.button('추천 메뉴로 돌아가기'):go('recommendations')
                st.stop()
    go('detail')

if st.session_state.page=='detail':
    idx=st.session_state.selected_recipe
    r=st.session_state.results[idx]
    detail=st.session_state.recipe_details[st.session_state.current_recipe_id]
    steps=[x for x in detail.get('steps_detail',[]) if isinstance(x,dict)]
    pages=[('intro',None),('ingredients',None),('preparation',None)]+[('step',x) for x in steps]+[('finish',None)]
    i=min(st.session_state.step_index,len(pages)-1)
    kind,content=pages[i]
    st.markdown('<div class="progresslabel">STEP 03 / 03 · 한 장씩 따라 하는 레시피</div>',unsafe_allow_html=True)
    st.title(r.get('name','상세 레시피'))
    st.progress((i+1)/len(pages))
    st.caption(f'📖 레시피 카드 {i+1} / {len(pages)} · 아래 버튼으로 다음 장을 넘겨보세요')
    if kind=='intro':
        st.markdown('### 🍽️ 완성 요리')
        photo=find_food_photo(detail.get('photo_search_term') or r.get('name',''))
        if photo and photo.get('url'):
            st.markdown('<div class="photo-frame">',unsafe_allow_html=True)
            st.image(photo['url'],width=430)
            st.markdown('</div>',unsafe_allow_html=True)
            st.caption('📷 Wikimedia Commons 참고 사진 · 실제 레시피와 다를 수 있음')
            if photo.get('page'):st.caption('사진 출처: '+photo['page'])
        else: st.info('현재 참고 사진을 찾지 못했어요. 조리법은 정상적으로 볼 수 있어요.')
        st.markdown('<div class="navcard">',unsafe_allow_html=True)
        st.write(detail.get('summary') or r.get('description',''))
        st.caption(f'⏱ 약 {r.get("minutes","?")}분 · {servings}인분')
        st.markdown('</div>',unsafe_allow_html=True)
    elif kind=='ingredients':
        st.markdown('### 🧺 필요한 재료')
        for ingredient in detail.get('ingredients_detail',[]):
            if isinstance(ingredient,dict):
                name=ingredient.get('name','재료')
                flag='🟢' if name in r.get('have',[]) else '🛒'
                st.markdown(f'**{flag} {name}** · {ingredient.get("amount","적당량")}')
        st.caption('🟢 보유 재료 · 🛒 구매 또는 확인이 필요한 재료')
    elif kind=='preparation':
        st.markdown('### 🔪 요리 전 준비')
        for n,item in enumerate(detail.get('preparation',[]),1):
            st.markdown(f'**{n}.** {item}')
    elif kind=='step':
        current_step=i-2
        st.markdown(f'### 🍳 조리 {current_step}단계 / {len(steps)}')
        st.markdown(f'#### {content.get("title","조리하기")}')
        st.markdown('<div class="recipe-step"><div class="mini-label">COOKING GUIDE</div><div class="steptext">'+str(content.get('instruction','')).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')+'</div></div>',unsafe_allow_html=True)
        if content.get('minutes'):st.info(f'⏱ 예상 소요 시간: {content["minutes"]}분')
    else:
        st.markdown('### 🎉 요리 완성!')
        if detail.get('plating'):st.write('🍽️ '+detail['plating'])
        if detail.get('tips'):
            st.markdown('#### 💡 요리 팁')
            for tip in detail['tips']:st.write('• '+str(tip))
        if detail.get('storage'):st.caption('보관: '+detail['storage'])
        if st.button('💚 이 레시피 저장',use_container_width=True):
            if r.get('name') not in [x.get('name') for x in st.session_state.saved]:
                st.session_state.saved.append(r)
            st.success('이 세션의 찜 목록에 저장했어요.')
    st.warning('AI 생성 레시피입니다. 알레르기, 교차접촉, 식재료 상태 및 충분한 가열 여부는 직접 확인하세요.')
    step_nav(len(pages))
    if st.button('← 추천 메뉴 목록으로',use_container_width=True):go('recommendations')

if st.session_state.saved:
    with st.sidebar.expander(f'💚 저장한 메뉴 ({len(st.session_state.saved)})'):
        for r in st.session_state.saved:st.write('• '+r.get('name',''))
        st.download_button('JSON 내보내기',json.dumps(st.session_state.saved,ensure_ascii=False,indent=2),file_name='tpowi_recipes.json',mime='application/json')

st.markdown('<div class="footer-note">MADE WITH 🧡 · TPOWI 2.0 · PERSONALIZED RECIPE EXPERIENCE</div>',unsafe_allow_html=True)
