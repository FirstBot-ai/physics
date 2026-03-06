# app.py
import streamlit as st
import requests
import base64
import random
import os
import time

# === НАСТРОЙКИ API (ОБНОВЛЕННЫЕ АДРЕСА) ===
# Пробуем основной домен gigachat.ru
GIGACHAT_TOKEN_URL = "https://gigachat.ru/api/v1/oauth"
GIGACHAT_CHAT_URL = "https://gigachat.ru/api/v1/chat/completions"

# Отключаем предупреждения об SSL (частая ошибка на хостингах)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === ИНИЦИАЛИЗАЦИЯ СЕССИИ ===
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Ты — бот-помощник по физике для студентов вузов. Отвечай ТОЛЬКО на вопросы, связанные с физикой. Если вопрос не по физике, вежливо откажись отвечать."}
    ]
if "quiz_answered" not in st.session_state:
    st.session_state.quiz_answered = False

# === СПИСОК ВИКТОРИНЫ (15 вопросов) ===
QUIZ_QUESTIONS = [
    {"question": "Какая единица измерения силы в системе СИ?", "options": ["А) Джоуль", "Б) Ньютон", "В) Ватт", "Г) Паскаль"], "correct": "Б", "explanation": "Сила измеряется в Ньютонах (Н)."},
    {"question": "Что такое инерция?", "options": ["А) Сила трения", "Б) Свойство тела сохранять скорость", "В) Ускорение тела", "Г) Энергия движения"], "correct": "Б", "explanation": "Инерция — свойство тела сохранять состояние покоя или движения."},
    {"question": "Формула второго закона Ньютона:", "options": ["А) F = mv", "Б) F = ma", "В) F = m/a", "Г) F = v/t"], "correct": "Б", "explanation": "Второй закон Ньютона: F = ma."},
    {"question": "Скорость света в вакууме приблизительно равна:", "options": ["А) 300 000 км/с", "Б) 150 000 км/с", "В) 1 000 000 км/с", "Г) 30 000 км/с"], "correct": "А", "explanation": "Скорость света c ≈ 300 000 км/с."},
    {"question": "Какой закон описывает сохранение энергии?", "options": ["А) Закон Ома", "Б) Закон сохранения импульса", "В) Закон сохранения энергии", "Г) Закон тяготения"], "correct": "В", "explanation": "В замкнутой системе энергия сохраняется."},
    {"question": "Что измеряется в Вольтах?", "options": ["А) Сила тока", "Б) Сопротивление", "В) Напряжение", "Г) Мощность"], "correct": "В", "explanation": "Вольт — единица измерения напряжения."},
    {"question": "Формула кинетической энергии:", "options": ["А) E = mgh", "Б) E = mv²/2", "В) E = mc²", "Г) E = Fd"], "correct": "Б", "explanation": "Кинетическая энергия: Eₖ = mv²/2."},
    {"question": "Какой тип волны является звуковая волна?", "options": ["А) Поперечная", "Б) Продольная", "В) Электромагнитная", "Г) Гравитационная"], "correct": "Б", "explanation": "Звуковая волна в газах — продольная."},
    {"question": "Период колебаний маятника зависит от:", "options": ["А) Массы груза", "Б) Амплитуды", "В) Длины маятника", "Г) Цвета груза"], "correct": "В", "explanation": "T = 2π√(l/g) — зависит от длины."},
    {"question": "Что такое абсолютный ноль температуры?", "options": ["А) 0°C", "Б) -100°C", "В) -273.15°C", "Г) -450°C"], "correct": "В", "explanation": "Абсолютный ноль = -273.15°C = 0 K."},
    {"question": "Закон Ома для участка цепи:", "options": ["А) I = U/R", "Б) I = UR", "В) I = R/U", "Г) I = U+R"], "correct": "А", "explanation": "Закон Ома: I = U/R."},
    {"question": "Какая сила действует на тело в жидкости?", "options": ["А) Сила Ампера", "Б) Сила Лоренца", "В) Сила Архимеда", "Г) Сила Кулона"], "correct": "В", "explanation": "Сила Архимеда выталкивает тело."},
    {"question": "Фотоэффект объяснил:", "options": ["А) Ньютон", "Б) Максвелл", "В) Эйнштейн", "Г) Бор"], "correct": "В", "explanation": "Эйнштейн объяснил фотоэффект (1905)."},
    {"question": "Единица измерения мощности в СИ:", "options": ["А) Джоуль", "Б) Ньютон", "В) Ватт", "Г) Герц"], "correct": "В", "explanation": "Мощность измеряется в Ваттах."},
    {"question": "Ускорение свободного падения на Земле:", "options": ["А) 5 м/с²", "Б) 9.8 м/с²", "В) 15 м/с²", "Г) 20 м/с²"], "correct": "Б", "explanation": "g ≈ 9.8 м/с²."}
]

# === ФУНКЦИИ ===
def test_connection():
    """Проверка доступности API"""
    try:
        # Пытаемся просто пингануть домен
        requests.get("https://gigachat.ru", timeout=5, verify=False)
        return True
    except:
        return False

def get_gigachat_token(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
        "Authorization": f"Basic {encoded}",
        "RqUID": "00000000-0000-0000-0000-000000000000"
    }
    data = {"scope": "GIGACHAT_API_PERS"}
    
    try:
        # verify=False отключает проверку SSL сертификата
        response = requests.post(GIGACHAT_TOKEN_URL, headers=headers, data=data, timeout=10, verify=False)
        
        if response.status_code == 200:
            return response.json()["access_token"]
        elif response.status_code == 401:
            st.error("❌ Ошибка 401: Неверный логин или пароль")
        elif response.status_code == 403:
            st.error("❌ Ошибка 403: Нет доступа к API")
        else:
            st.error(f"❌ Ошибка {response.status_code}: {response.text}")
        return None
        
    except requests.exceptions.SSLError:
        st.error("🔒 Ошибка SSL сертификата. Попробуем без проверки...")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"🌐 Ошибка соединения: {e}")
        st.info("💡 Возможно, сервер GigaChat недоступен из-за границы или заблокирован.")
        return None
    except Exception as e:
        st.error(f"❌ Ошибка: {e}")
        return None

def ask_gigachat(token, messages):
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "model": "GigaChat", 
        "messages": messages, 
        "temperature": 0.3
    }
    
    try:
        response = requests.post(GIGACHAT_CHAT_URL, headers=headers, json=payload, timeout=30, verify=False)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ Ошибка API: {response.status_code}\n{response.text}"
    except Exception as e:
        return f"❌ Ошибка запроса: {e}"

# === ИНТЕРФЕЙС ===
st.set_page_config(page_title="Физика Бот", page_icon="⚛️")
st.title("⚛️ Физика Бот")

# === ДИАГНОСТИКА СЕТИ ===
with st.expander("📡 Диагностика сети (нажми, если не работает)"):
    if st.button("Проверить доступность GigaChat"):
        with st.spinner("Проверка..."):
            if test_connection():
                st.success("✅ Сервер GigaChat доступен!")
            else:
                st.error("❌ Сервер GigaChat НЕ доступен из Railway!")
                st.warning("⚠️ Попробуйте локальный запуск или сменить хостинг.")

# === БОКОВАЯ ПАНЕЛЬ ===
with st.sidebar:
    st.header("🔑 Настройки")
    env_id = os.environ.get("GIGACHAT_CLIENT_ID", "")
    env_secret = os.environ.get("GIGACHAT_CLIENT_SECRET", "")
    
    client_id = st.text_input("Client ID", type="password", value=env_id)
    client_secret = st.text_input("Client Secret", type="password", value=env_secret)
    
    if env_id:
        st.success("✅ Key loaded")
    else:
        st.warning("⚠️ No Key found")

# === ЧАТ ===
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Задайте вопрос по физике..."):
    if not client_id or not client_secret:
        st.error("⚠️ Введите ключи!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Думаю..."):
                token = get_gigachat_token(client_id, client_secret)
                if token:
                    response = ask_gigachat(token, st.session_state.messages)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

# === ВИКТОРИНА ===
st.divider()
st.subheader("🎓 Мини-викторина")
if st.button("🎲 Случайный вопрос"):
    st.session_state.current_quiz = random.choice(QUIZ_QUESTIONS)
    st.session_state.quiz_answered = False

if "current_quiz" in st.session_state and not st.session_state.quiz_answered:
    q = st.session_state.current_quiz
    st.markdown(f"**{q['question']}**")
    for opt in q["options"]:
        st.write(opt)
    answer = st.text_input("Ответ (А, Б, В, Г):", key="quiz_input").strip().upper()
    if st.button("Проверить"):
        if answer in ["А", "Б", "В", "Г"]:
            if answer == q["correct"]:
                st.success("✅ Верно!")
            else:
                st.error(f"❌ Нет. Правильно: {q['correct']}")
            st.info(f"💡 {q['explanation']}")
            st.session_state.quiz_answered = True

st.caption("Проект в учебных целях")
