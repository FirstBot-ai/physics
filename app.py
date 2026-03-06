# app.py
import streamlit as st
import requests
import base64
import random
import os
import time
import urllib3

# Отключаем предупреждения о SSL сертификатах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === НАСТРОЙКИ API ===
GIGACHAT_TOKEN_URL = "POST /api/v2/oauth"
GIGACHAT_CHAT_URL = "https://gigachat.devices.sberbank.ru/"
TIMEOUT_TOKEN = 30  # Увеличенный таймаут для токена
TIMEOUT_CHAT = 60   # Увеличенный таймаут для чата

# === ИНИЦИАЛИЗАЦИЯ СЕССИИ ===
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Ты — бот-помощник по физике для студентов вузов. Отвечай ТОЛЬКО на вопросы, связанные с физикой. Если вопрос не по физике (например, про рецепты, историю, биологию и т.д.), вежливо откажись отвечать и предложи задать вопрос по физике. Объясняй четко, с использованием формул если нужно, но доступно."}
    ]
if "quiz_answered" not in st.session_state:
    st.session_state.quiz_answered = False

# === СПИСОК ВИКТОРИНЫ (15 вопросов) ===
QUIZ_QUESTIONS = [
    {"question": "Какая единица измерения силы в системе СИ?", "options": ["А) Джоуль", "Б) Ньютон", "В) Ватт", "Г) Паскаль"], "correct": "Б", "explanation": "Сила измеряется в Ньютонах (Н). 1 Н = 1 кг·м/с²"},
    {"question": "Что такое инерция?", "options": ["А) Сила трения", "Б) Свойство тела сохранять скорость", "В) Ускорение тела", "Г) Энергия движения"], "correct": "Б", "explanation": "Инерция — свойство тела сохранять состояние покоя или равномерного прямолинейного движения (1-й закон Ньютона)"},
    {"question": "Формула второго закона Ньютона:", "options": ["А) F = mv", "Б) F = ma", "В) F = m/a", "Г) F = v/t"], "correct": "Б", "explanation": "Второй закон Ньютона: F = ma, где F — сила, m — масса, a — ускорение"},
    {"question": "Скорость света в вакууме приблизительно равна:", "options": ["А) 300 000 км/с", "Б) 150 000 км/с", "В) 1 000 000 км/с", "Г) 30 000 км/с"], "correct": "А", "explanation": "Скорость света в вакууме c ≈ 299 792 458 м/с ≈ 300 000 км/с"},
    {"question": "Какой закон описывает сохранение энергии?", "options": ["А) Закон Ома", "Б) Закон сохранения импульса", "В) Закон сохранения энергии", "Г) Закон всемирного тяготения"], "correct": "В", "explanation": "В замкнутой системе полная энергия сохраняется, лишь переходя из одной формы в другую"},
    {"question": "Что измеряется в Вольтах?", "options": ["А) Сила тока", "Б) Сопротивление", "В) Напряжение", "Г) Мощность"], "correct": "В", "explanation": "Вольт (В) — единица измерения электрического напряжения (разности потенциалов)"},
    {"question": "Формула кинетической энергии:", "options": ["А) E = mgh", "Б) E = mv²/2", "В) E = mc²", "Г) E = Fd"], "correct": "Б", "explanation": "Кинетическая энергия: Eₖ = mv²/2, где m — масса, v — скорость"},
    {"question": "Какой тип волны является звуковая волна?", "options": ["А) Поперечная", "Б) Продольная", "В) Электромагнитная", "Г) Гравитационная"], "correct": "Б", "explanation": "Звуковая волна в газах и жидкостях — продольная: частицы колеблются вдоль направления распространения"},
    {"question": "Период колебаний маятника зависит от:", "options": ["А) Массы груза", "Б) Амплитуды", "В) Длины маятника", "Г) Цвета груза"], "correct": "В", "explanation": "T = 2π√(l/g) — зависит от длины l и ускорения свободного падения g"},
    {"question": "Что такое абсолютный ноль температуры?", "options": ["А) 0°C", "Б) -100°C", "В) -273.15°C", "Г) -450°C"], "correct": "В", "explanation": "Абсолютный ноль = -273.15°C = 0 K — температура, при которой прекращается тепловое движение частиц"},
    {"question": "Закон Ома для участка цепи:", "options": ["А) I = U/R", "Б) I = UR", "В) I = R/U", "Г) I = U+R"], "correct": "А", "explanation": "Закон Ома: I = U/R, где I — ток, U — напряжение, R — сопротивление"},
    {"question": "Какая сила действует на тело, погруженное в жидкость?", "options": ["А) Сила Ампера", "Б) Сила Лоренца", "В) Сила Архимеда", "Г) Сила Кулона"], "correct": "В", "explanation": "Сила Архимеда выталкивает тело и равна весу вытесненной жидкости"},
    {"question": "Фотоэффект объяснил:", "options": ["А) Ньютон", "Б) Максвелл", "В) Эйнштейн", "Г) Бор"], "correct": "В", "explanation": "Эйнштейн объяснил фотоэффект (1905), предположив, что свет состоит из квантов (фотонов)"},
    {"question": "Единица измерения мощности в СИ:", "options": ["А) Джоуль", "Б) Ньютон", "В) Ватт", "Г) Герц"], "correct": "В", "explanation": "Мощность измеряется в Ваттах (Вт). 1 Вт = 1 Дж/с"},
    {"question": "Ускорение свободного падения на Земле приблизительно:", "options": ["А) 5 м/с²", "Б) 9.8 м/с²", "В) 15 м/с²", "Г) 20 м/с²"], "correct": "Б", "explanation": "g ≈ 9.8 м/с² (часто округляют до 10 м/с² для упрощения расчетов)"}
]

# === ФУНКЦИИ ===
def get_gigachat_token(client_id, client_secret, max_retries=2):
    """Получение токена авторизации от GigaChat с повторными попытками"""
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
        "Authorization": f"Basic {encoded}",
        "RqUID": "00000000-0000-0000-0000-000000000000"
    }
    data = {"scope": "GIGACHAT_API_PERS"}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(GIGACHAT_TOKEN_URL, headers=headers, data=data, timeout=TIMEOUT_TOKEN, verify=False)
            
            if response.status_code == 200:
                return response.json()["access_token"]
            elif response.status_code == 401:
                st.error("❌ Ошибка 401: Неверный Client ID или Client Secret")
                st.info("💡 Проверьте ключи в GigaDev кабинете")
                return None
            elif response.status_code == 403:
                st.error("❌ Ошибка 403: У ключей нет прав доступа к API")
                return None
            elif response.status_code in [502, 503, 504]:
                if attempt < max_retries - 1:
                    st.warning(f"⏳ Сервер занят (попытка {attempt+1}/{max_retries})...")
                    time.sleep(3)
                    continue
                else:
                    st.error("❌ Сервер GigaChat временно недоступен. Попробуйте позже.")
                    return None
            else:
                st.error(f"❌ Ошибка авторизации: {response.status_code}")
                st.error(f"📄 Ответ: {response.text[:200]}")
                return None
                
        except requests.exceptions.ReadTimeout:
            if attempt < max_retries - 1:
                st.warning("⏱️ Таймаут, повторная попытка...")
                time.sleep(3)
                continue
            st.error("⏱️ Превышено время ожидания ответа от GigaChat")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🌐 Ошибка соединения: Проверьте интернет")
            return None
        except Exception as e:
            st.error(f"❌ Неожиданная ошибка: {e}")
            return None
    
    return None

def ask_gigachat(token, messages, max_retries=2):
    """Отправка запроса к GigaChat с повторными попытками"""
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "model": "GigaChat", 
        "messages": messages, 
        "temperature": 0.3
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(GIGACHAT_CHAT_URL, headers=headers, json=payload, timeout=TIMEOUT_CHAT, verify=False)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 401:
                return "❌ Ошибка: Токен недействителен. Проверьте ключи."
            elif response.status_code == 429:
                return "⏳ Ошибка: Слишком много запросов. Подождите немного."
            elif response.status_code in [502, 503, 504]:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                else:
                    return "❌ Сервер временно недоступен (502). Попробуйте через минуту."
            else:
                return f"❌ Ошибка API: {response.status_code}\n📄 {response.text[:200]}"
                
        except requests.exceptions.ReadTimeout:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return "⏱️ Сервер не ответил вовремя. Попробуйте ещё раз."
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    return "❌ Не удалось получить ответ после нескольких попыток"

# === ИНТЕРФЕЙС ===
st.set_page_config(page_title="Физика Бот", page_icon="⚛️")
st.title("⚛️ Физика Бот")

# === ДИАГНОСТИКА СЕТИ ===
with st.expander("📡 Диагностика сети (нажми, если не работает)"):
    if st.button("Проверить доступность GigaChat"):
        with st.spinner("Проверка..."):
            try:
                test_resp = requests.get("https://gigachat.devices.sberbank.ru", timeout=10, verify=False)
                st.success(f"✅ Сервер доступен! Статус: {test_resp.status_code}")
            except Exception as e:
                st.error(f"❌ Сервер недоступен: {e}")
                st.warning("⚠️ Попробуйте локальный запуск или подождите")

# === БОКОВАЯ ПАНЕЛЬ С КЛЮЧАМИ ===
with st.sidebar:
    st.header("🔑 Настройки")
    
    # Автоматическая загрузка из Railway Variables
    env_id = os.environ.get("GIGACHAT_CLIENT_ID", "")
    env_secret = os.environ.get("GIGACHAT_CLIENT_SECRET", "")
    
    client_id = st.text_input("Client ID", type="password", value=env_id)
    client_secret = st.text_input("Client Secret", type="password", value=env_secret)
    
    if env_id or env_secret:
        st.success("✅ Ключи загружены из Railway Variables")
        st.info(f"ID: `{env_id[:4]}...`")
    else:
        st.warning("⚠️ Введите ключи вручную или добавьте Variables в Railway")
    
    st.caption("💡 Ключи не сохраняются в логах")

# === ОТОБРАЖЕНИЕ ЧАТА ===
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# === ОБРАБОТКА ВВОДА ПОЛЬЗОВАТЕЛЯ ===
if prompt := st.chat_input("Задайте вопрос по физике..."):
    if not client_id or not client_secret:
        st.error("⚠️ Введите Client ID и Client Secret в настройках слева!")
    else:
        # Добавляем сообщение пользователя в историю
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Думаю..."):
                token = get_gigachat_token(client_id, client_secret)
                
                if token:
                    response = ask_gigachat(token, st.session_state.messages)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("❌ Не удалось получить токен. Проверьте ключи и логи выше.")

# === ВИКТОРИНА ===
st.divider()
st.subheader("🎓 Мини-викторина")

col1, col2 = st.columns([3, 1])
with col1:
    st.write("Нажми кнопку, чтобы получить случайный вопрос по физике!")
with col2:
    if st.button("🎲 Случайный вопрос"):
        st.session_state.current_quiz = random.choice(QUIZ_QUESTIONS)
        st.session_state.quiz_answered = False

if "current_quiz" in st.session_state and not st.session_state.quiz_answered:
    q = st.session_state.current_quiz
    st.markdown(f"**{q['question']}**")
    for opt in q["options"]:
        st.write(opt)
    
    answer = st.text_input("Ваш ответ (введите букву А, Б, В или Г):", key="quiz_input").strip().upper()
    
    if st.button("Проверить ответ"):
        if answer in ["А", "Б", "В", "Г"]:
            if answer == q["correct"]:
                st.success("✅ Правильно!")
            else:
                st.error(f"❌ Неправильно. Правильный ответ: {q['correct']}")
            st.info(f"💡 {q['explanation']}")
            st.session_state.quiz_answered = True
        else:
            st.warning("⚠️ Введите одну букву: А, Б, В или Г")

st.divider()
st.caption("Проект в учебных целях | Физика + GigaChat + Streamlit + Railway")
