from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
from dotenv import load_dotenv
from input_texts import INPUT_TEXTS  # 입력 텍스트 파일 임포트

load_dotenv()

def sleep(seconds=3):
    time.sleep(seconds)

def login_to_google(driver, credentials):
    try:
        driver.get('https://accounts.google.com')
        sleep()

        print("이메일 입력 중...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
        )
        email_field.clear()
        email_field.send_keys(credentials['email'])
        sleep(1)
        
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#identifierNext button'))
        )
        next_button.click()
        sleep(4)  # 2초에서 4초로 증가

        print("비밀번호 입력 중...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
        )
        password_field.clear()
        password_field.send_keys(credentials['password'])
        sleep(1)

        password_next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#passwordNext button'))
        )
        password_next_button.click()
        sleep(8)  # 5초에서 8초로 증가

        try:
            error_message = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.o6cuMc'))
            )
            print(f"로그인 오류: {error_message.text}")
            return False
        except TimeoutException:
            print("로그인 성공!")
            return True

    except Exception as e:
        print(f"로그인 중 오류 발생: {str(e)}")
        return False

def process_single_text(driver, input_text, text_number):
    try:
        print(f"\n{text_number}번째 텍스트 처리 시작...")
        
        print("NotebookLM으로 이동 중...")
        driver.get('https://notebooklm.google.com/')
        sleep(5)
        
        print("새로 만들기 버튼 찾는 중...")
        new_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.create-new-label'))
        )
        new_button.click()
        sleep()
        
        print("복사된 텍스트 옵션 찾는 중...")
        text_labels = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.mdc-evolution-chip__text-label'))
        )
        for label in text_labels:
            if '복사된 텍스트' in label.text:
                label.click()
                break
        sleep()
        
        print("텍스트 입력 중...")
        # 텍스트 영역을 찾기 위한 여러 셀렉터 시도
        textarea_selectors = [
            "textarea.mat-mdc-input-element",
            "#mat-input-1",
            "#mat-input-2",
            "textarea[formcontrolname='text']",
            "textarea.mat-mdc-form-field-textarea-control"
        ]
        
        textarea = None
        for selector in textarea_selectors:
            try:
                textarea = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if textarea:
                    break
            except TimeoutException:
                continue
        
        if not textarea:
            # 텍스트 영역을 찾지 못한 경우 라벨을 통해 시도
            try:
                label = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//mat-label[contains(text(), '여기에 텍스트를 붙여넣으세요')]"))
                )
                label.click()
                sleep(1)
                textarea = driver.switch_to.active_element
            except Exception as e:
                print(f"텍스트 영역을 찾을 수 없습니다: {e}")
                raise
        
        # 텍스트 입력 시도
        textarea.click()
        sleep(1)
        textarea.clear()
        sleep(1)
        textarea.send_keys(input_text)
        sleep(10)
        
        print("삽입 버튼 찾는 중...")
        insert_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.xpath, "//span[contains(@class, 'mdc-button__label') and text()='삽입']"))
        )
        insert_button.click()
        sleep()
        
        print("생성 버튼 찾는 중...")
        generate_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.xpath, "//span[contains(@class, 'mdc-button__label') and text()='생성']"))
        )
        generate_button.click()
        sleep(10)
        
        print(f"{text_number}번째 텍스트 처리 완료!")
        return True

    except Exception as e:
        print(f'{text_number}번째 텍스트 처리 중 오류 발생: {e}')
        return False

def automate_notebook_lm():
    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    
    try:
        # User Agent 설정
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Google 로그인
        credentials = {
            'email': os.getenv('GOOGLE_EMAIL'),
            'password': os.getenv('GOOGLE_PASSWORD')
        }
        
        if not login_to_google(driver, credentials):
            print("로그인 실패. 프로그램을 종료합니다.")
            return

        # 각 텍스트에 대해 처리
        for idx, text in enumerate(INPUT_TEXTS, 1):
            success = process_single_text(driver, text, idx)
            if not success:
                print(f"{idx}번째 텍스트 처리 실패. 다음 텍스트로 진행합니다.")
            sleep(3)  # 다음 텍스트 처리 전 대기

        print("\n모든 텍스트 처리 완료!")
        input("아무 키나 누르면 브라우저가 종료됩니다...")
        
    except Exception as e:
        print(f'오류 발생: {e}')
    finally:
        driver.quit()

if __name__ == "__main__":
    automate_notebook_lm()