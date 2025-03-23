"""Bing搜索工具

该模块提供了使用Selenium在Bing搜索引擎上进行搜索的工具。
工具会打开浏览器，访问Bing搜索页面，输入搜索内容，并返回搜索结果。
"""

import logging
import os
import platform
import time
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ACC.tool.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)

class SearchBingTool(BaseTool):
    """Bing搜索工具"""

    def __init__(self):
        """初始化Bing搜索工具"""
        super().__init__(
            name="search_bing",
            description="在Bing搜索引擎上搜索指定内容并返回搜索结果，包含网页标题、链接和内容摘要"
        )

    def _get_chromedriver_path(self) -> str:
        """获取适合当前操作系统的ChromeDriver路径

        Returns:
            ChromeDriver可执行文件的绝对路径
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if platform.system() == "Windows":
            chromedriver_dir = os.path.join(base_dir, "chromedriver", "chromedriver-win64")
            chromedriver_path = os.path.join(chromedriver_dir, "chromedriver.exe")
        else:  # Linux或其他系统
            chromedriver_dir = os.path.join(base_dir, "chromedriver", "chromedriver-linux64")
            chromedriver_path = os.path.join(chromedriver_dir, "chromedriver")
        
        logger.debug(f"ChromeDriver路径: {chromedriver_path}")
        return chromedriver_path
    
    def _get_page_content_with_browser(self, url: str, driver, timeout: int = 30, max_chars: int = 600) -> str:
        """使用浏览器获取网页内容

        Args:
            url: 网页URL
            driver: WebDriver实例
            timeout: 等待页面加载的超时时间（秒）
            max_chars: 最大字符数，默认600

        Returns:
            网页内容摘要，超过max_chars会被截断
        """
        try:
            # 保存当前窗口句柄
            original_window = driver.current_window_handle
            
            # 打开新标签页
            driver.execute_script("window.open('');")
            
            # 切换到新标签页
            driver.switch_to.window(driver.window_handles[-1])
            
            # 访问URL
            logger.info(f"正在访问网页: {url}")
            driver.get(url)
            
            # 等待页面加载完成
            logger.info("等待页面完全加载...")
            time.sleep(2)
            
            # 等待body元素加载
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 给页面一些时间完全加载
            logger.info("页面已加载，等待2秒以确保页面完全渲染...")
            time.sleep(2)
            
            # 获取页面文本内容
            body_element = driver.find_element(By.TAG_NAME, "body")
            text = body_element.text
            
            # 清理文本（移除多余空格）
            text = ' '.join(text.split())
            
            # 截断文本
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            # 关闭当前标签页并切回原标签页
            driver.close()
            driver.switch_to.window(original_window)
            
            return text
        except Exception as e:
            logger.warning(f"使用浏览器获取网页内容失败: {e}")
            
            # 尝试切回原标签页
            try:
                if driver.current_window_handle != original_window:
                    driver.close()
                    driver.switch_to.window(original_window)
            except:
                pass
                
            return "无法获取网页内容"

    def execute(self, query: str, max_results: int = 5, timeout: int = 30, fetch_content: bool = True) -> Dict[str, Any]:
        """执行Bing搜索操作

        Args:
            query: 搜索查询内容
            max_results: 返回的最大结果数量，默认为5
            timeout: 等待页面加载的超时时间（秒），默认为30秒
            fetch_content: 是否获取网页内容，默认为True

        Returns:
            执行结果字典，包含搜索结果
        """
        driver = None
        try:
            # 设置Chrome选项
            chrome_options = Options()
            # chrome_options.add_argument("--start-maximized")  # 最大化窗口
            chrome_options.add_argument("--disable-extensions")  # 禁用扩展
            chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速
            chrome_options.add_argument("--no-sandbox")  # 禁用沙盒模式
            
            # 获取ChromeDriver路径
            chromedriver_path = self._get_chromedriver_path()
            
            # 创建Service对象
            service = Service(executable_path=chromedriver_path)
            
            # 创建WebDriver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置隐式等待时间
            driver.implicitly_wait(10)
            
            # 访问Bing搜索页面
            logger.info(f"正在访问Bing搜索页面，搜索内容: {query}")
            driver.get("https://www.bing.com")
            
            # 等待页面完全加载后额外等待2秒
            logger.info("等待页面完全加载...")
            time.sleep(2)
            
            # 等待搜索框加载
            search_box = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            
            # 清空搜索框并输入搜索内容
            search_box.clear()
            search_box.send_keys(query)
            
            # 提交搜索
            search_box.send_keys(Keys.RETURN)
            
            # 等待搜索结果加载
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )
            
            # 给页面一些时间完全加载 - 增加等待时间到2秒
            logger.info("搜索结果已加载，等待2秒以确保页面完全渲染...")
            time.sleep(2)
            
            # 获取搜索结果
            search_results = []
            result_elements = driver.find_elements(By.CSS_SELECTOR, "#b_results .b_algo")
            
            # 限制结果数量
            for i, element in enumerate(result_elements):
                if i >= max_results:
                    break
                
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, "h2 a")
                    title = title_element.text
                    url = title_element.get_attribute("href")
                    
                    # 尝试获取描述
                    try:
                        description = element.find_element(By.CSS_SELECTOR, ".b_caption p").text
                    except:
                        description = "无描述"
                    
                    # 使用浏览器获取网页内容
                    page_content = "未获取网页内容"
                    if fetch_content and url:
                        logger.info(f"准备获取网页内容: {url}")
                        page_content = self._get_page_content_with_browser(url, driver, timeout)
                    
                    search_results.append({
                        "title": title,
                        "url": url,
                        "description": description,
                        "page_content": page_content
                    })
                except Exception as e:
                    logger.warning(f"提取搜索结果时出错: {e}")
            
            # 获取页面标题和URL
            page_title = driver.title
            page_url = driver.current_url
            
            logger.info(f"成功获取Bing搜索结果，共{len(search_results)}条")
            
            return {
                "status": "success",
                "message": f"成功获取Bing搜索结果，共{len(search_results)}条",
                "query": query,
                "page_title": page_title,
                "page_url": page_url,
                "results": search_results
            }
            
        except TimeoutException:
            logger.error(f"等待页面元素超时")
            return {
                "status": "error",
                "message": "等待页面元素超时，请检查网络连接或增加超时时间",
                "query": query
            }
        except WebDriverException as e:
            logger.error(f"WebDriver错误: {e}")
            return {
                "status": "error",
                "message": f"WebDriver错误: {str(e)}",
                "query": query
            }
        except Exception as e:
            logger.error(f"执行Bing搜索时发生错误: {e}")
            import traceback
            logger.debug(f"异常堆栈: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"执行Bing搜索失败: {str(e)}",
                "query": query
            }
        finally:
            # 关闭浏览器
            if driver:
                try:
                    driver.quit()
                    logger.info("已关闭浏览器")
                except Exception as e:
                    logger.error(f"关闭浏览器时出错: {e}")


# 注册工具
ToolRegistry.register(SearchBingTool())