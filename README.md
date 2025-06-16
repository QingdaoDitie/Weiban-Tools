# 安全微伴 (Anquan Weiban) 助手

这是一个用于“安全微伴”平台的半自动化学习和考试助手，旨在帮助用户自动化处理课程学习和在线考试。项目基于 `Python`，通过模拟接口请求实现功能。


**Author:** [@QingdaoDitie](https://github.com/QingdaoDitie)
**Version:** 1.0.0

-----

## 声明 (Disclaimer)

**本项目仅用于教育和学习目的。**

用户应自行承担使用此脚本可能带来的一切风险。开发者对任何因使用此工具而导致的账号问题或其他后果概不负责。请遵守平台的用户协议和相关规定。


-----

## 功能特性 (Features)

本项目包含两个主要模块：**课程学习 (刷课)** 和 **在线考试 (答题)**。

#### 1\. 课程学习助手 (`project.py`)

  - **自动登录**: 使用账号、密码和学校ID自动登录平台。
  - **验证码识别**: 自动调用第三方API识别和填写登录验证码。
  - **课程遍历**: 自动获取所有未完成的课程和章节列表。
  - **模拟学习**:
      - 模拟观看视频课程的全过程。
      - 包含随机延迟，模拟人类学习行为。
      - 自动处理和验证学习过程中的滑动验证码。
  - **进度跟踪**: 在控制台实时输出当前学习的课程、章节和进度。

#### 2\. 考试助手 (`paper.py`)

  - **题库构建**:
      - 自动拉取已完成的历史考试记录。
      - 从历史试卷中提取题目和正确答案，构建本地JSON格式的题库 (`question_bank`)。
  - **自动答题**:
      - 开始新考试后，自动从本地题库中匹配题目并填写答案。
      - 使用模糊匹配算法 (`find_longest_common_substring`) 提高题目匹配成功率。
  - **AI辅助答题 (可选)**:
      - 对于题库中不存在的题目，脚本预留了通过调用 **DeepSeek API** 进行AI答题的接口 (代码中默认注释)。
  - **自动提交**: 完成所有题目后，自动提交试卷并显示最终得分。

-----

## 环境准备 (Prerequisites)

在运行脚本之前，请确保您已配置好以下环境：

1.  **Python 3.x**
2.  **必要的 Python 库**:
    ```bash
    pip install requests pycryptodome pyexecjs openai
    ```
3.  **JavaScript 运行环境**: `PyExecJS` 需要一个JS运行时，如 `Node.js`。
4.  **`demo.js` 文件**: `project.py` 依赖一个名为 `demo.js` 的文件来生成API请求签名。您需要自行准备此文件并将其与 `project.py` 放置在同一目录下。
5.  **API Keys**:
      * **打码平台 Token**: 脚本使用 `jfbym.com` API来识别验证码。请在 `project.py` 和 `paper.py` 中填入您的有效Token。
      * **DeepSeek API Key (可选)**: 如果您希望使用AI答题功能，需要在 `paper.py` 中填入您的 DeepSeek API Key。

-----

## 配置和使用 (Configuration and Usage)

#### 步骤 1: 克隆或下载项目

将项目文件下载到您的本地计算机。

#### 步骤 2: 配置脚本

打开 `project.py` 和 `paper.py` 文件，根据注释修改以下变量：

**在 `project.py` (课程学习) 中:**

```python
# ...
key = "YOUR_CAPTCHA_API_TOKEN" # 在此处填入您的打码平台Token

if __name__ == '__main__':
    logger.info("Starting")

    username = 'YOUR_USERNAME'  # 您的学号或账号
    password = 'YOUR_PASSWORD'  # 您的密码
    school_id = "YOUR_SCHOOL_ID" # 您的学校ID
# ...
```

**在 `paper.py` (考试助手) 中:**
首先，您需要通过 `project.py` 登录一次，从其输出中获取 `token`, `userId` 和 `userProjectId`。

```python
# ...
def recon_image(image_base64):
    # ...
    token = "YOUR_CAPTCHA_API_TOKEN" # 在此处填入您的打码平台Token
    # ...

if __name__ == '__main__':
    key = "YOUR_DEEPSEEK_API_KEY"  # 在此处填入您的 DeepSeek API key
    session.headers["x-token"] = "YOUR_X_TOKEN" # 填入从登录后获取的 x-token
    session.headers["token"] = "YOUR_TOKEN"     # 填入从登录后获取的 token

    school_id = 'YOUR_SCHOOL_ID' # 您的学校ID

    userid = 'YOUR_USER_ID' # 您的用户ID
    userProjectId = 'YOUR_USER_PROJECT_ID' # 您需要考试的课程项目ID
# ...
```

#### 步骤 3: 运行脚本

1.  **完成课程学习**:
    首先运行课程学习脚本，确保所有视频课程都已完成。

    ```bash
    python project.py
    ```

    脚本将开始自动学习，并在控制台打印详细日志。

2.  **进行在线考试**:
    课程完成后，运行考试助手。脚本会首先尝试拉取历史记录以建立题库，然后开始答题。

    ```bash
    python paper.py
    ```

    脚本会自动完成答题和提交过程，并最终显示分数。

-----

## 项目文件结构

```
.
├── project.py            # 课程学习主脚本
├── paper.py              # 考试助手主脚本
├── demo.js               # (需自行准备) 用于生成请求签名的JS文件
└── readme.md             # 本说明文件
```
