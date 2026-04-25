import re
import threading
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.models import User, Role
import logging


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # 启动 Edge（使用 Selenium 自动管理驱动）
        options = webdriver.EdgeOptions()
        options.add_argument('headless')
        try:
            cls.client = webdriver.Edge(options=options)
            # 设置隐式等待
            cls.client.implicitly_wait(10)
        except Exception as e:
            print(f"Failed to start Edge: {e}")
            pass

        # 如果无法启动浏览器，跳过这些测试
        if cls.client:
            # 创建应用
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # 禁止日志，保持输出简洁
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # 创建数据库，并使用一些虚拟数据填充
            db.create_all()
            Role.insert_roles()

            # 添加管理员
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='john@example.com', username='john',
                        password='cat', role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # 在一个线程中启动 Flask 服务器
            from werkzeug.serving import make_server
            cls.server = make_server('127.0.0.1', 5000, cls.app)
            cls.server_thread = threading.Thread(target=cls.server.serve_forever)
            cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            try:
                # 先关闭浏览器
                cls.client.quit()
                print("Browser closed")
            except Exception as e:
                print(f"Error closing browser: {e}")
            
            try:
                # 使用线程关闭服务器
                import threading
                def shutdown_server():
                    cls.server.shutdown()
                
                shutdown_thread = threading.Thread(target=shutdown_server)
                shutdown_thread.daemon = True
                shutdown_thread.start()
                shutdown_thread.join(timeout=3)
                print("Server shutdown initiated")
            except Exception as e:
                print(f"Error shutting down server: {e}")
            
            try:
                cls.server_thread.join(timeout=2)
            except:
                pass

            # 销毁数据库
            try:
                db.session.remove()
                db.drop_all()
            except:
                pass

            # 删除应用上下文
            try:
                cls.app_context.pop()
            except:
                pass
            
            print("Cleanup completed")

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        # 进入首页
        print("Navigating to http://127.0.0.1:5000/...")
        self.client.get('http://127.0.0.1:5000/')
        
        # 等待页面加载
        import time
        time.sleep(2)
        
        print(f"Page title: {self.client.title}")
        print(f"Current URL: {self.client.current_url}")
        
        self.assertTrue('Welcome!' in self.client.page_source)
        print("✓ Found 'Welcome!'")

        # 使用 JS 点击登录链接
        print("\nClicking login link...")
        login_link = self.client.find_element(By.CSS_SELECTOR, 'a[href*="/auth/login"]')
        print(f"Found login link: {login_link.get_attribute('href')}")
        self.client.execute_script("arguments[0].click();", login_link)
        
        # 等待登录页面加载
        time.sleep(3)
        print(f"Login page title: {self.client.title}")
        print(f"Login page URL: {self.client.current_url}")
        self.assertTrue('登录' in self.client.page_source or 'Login' in self.client.page_source)
        print("✓ On login page")

        # 登录
        print("\nFilling login form...")
        email_field = self.client.find_element(By.NAME, 'email')
        password_field = self.client.find_element(By.NAME, 'password')
        submit_button = self.client.find_element(By.NAME, 'submit')
        print("Found all form fields")
        
        email_field.clear()
        email_field.send_keys('john@example.com')
        password_field.clear()
        password_field.send_keys('cat')
        
        print("Submitting form...")
        submit_button.click()
        
        # 等待登录完成
        time.sleep(3)
        print(f"After login, current URL: {self.client.current_url}")
        print(f"After login, page title: {self.client.title}")
        
        # 保存登录后页面
        with open('debug_after_login.html', 'w', encoding='utf-8') as f:
            f.write(self.client.page_source)
        print("Saved to debug_after_login.html")
        
        # 检查是否登录成功
        if re.search(r'Hello,\s+john!', self.client.page_source):
            print("✓ Logged in successfully")
        else:
            print("✗ Login failed or redirected elsewhere")
            print("Page source snippet (first 500 chars):")
            print(self.client.page_source[:500])
        
        self.assertTrue(re.search(r'Hello,\s+john!', self.client.page_source))

        # 进入用户资料页面
        print("\nClicking profile link...")
        profile_link = self.client.find_element(By.CSS_SELECTOR, 'a[href*="/user/"]')
        self.client.execute_script("arguments[0].click();", profile_link)
        
        # 等待个人资料页面加载
        time.sleep(2)
        self.assertIn('<h1>john</h1>', self.client.page_source)
        print("✓ On profile page")
