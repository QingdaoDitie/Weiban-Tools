"""/*
 * @author: @QingdaoDitie
 * @date: 2025/05/23
 * @description:安全微伴 半自动考试 需要一定编程基础 有时间合并到一起
 * @version: 1.0.0
 * @contact: https://github.com/QingdaoDitie
 */"""
import base64
import logging
import re
import time
import random
from openai import OpenAI

import json
import requests
from requests.exceptions import RequestException


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志记录的最低级别

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# # 创建文件处理器，用于写入日志文件
# file_handler = logging.FileHandler('weiban_study.log', encoding='utf-8')
# file_handler.setFormatter(formatter)

# 创建控制台处理器，用于输出到控制台
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
#
# # 将处理器添加到记录器
# logger.addHandler(file_handler)
logger.addHandler(console_handler)

session = requests.Session()

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
    'origin': 'https://weiban.mycourse.cn',
    'priority': 'u=1, i',
    'referer': 'https://weiban.mycourse.cn/',
    'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
}

def find_longest_common_substring(s1, s2):
    """查找两个字符串的最长公共连续子串"""
    m = len(s1)
    n = len(s2)
    max_len = 0
    end_idx = 0
    # 创建二维数组记录最长公共子串长度
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    end_idx = i  # 记录子串在s1中的结束位置
            else:
                dp[i][j] = 0
    # 返回最长公共子串及其长度
    if max_len == 0:
        return "", 0
    longest_sub = s1[end_idx - max_len: end_idx]
    return longest_sub, max_len

def is_substring_matched(question_text, bank_text, threshold_ratio=0.7):
    """判断是否满足重复片段匹配条件"""
    # 预处理：去除符号和空格（与题库预处理逻辑一致）
    q_clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', question_text)
    b_clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', bank_text)

    # 查找最长公共子串
    longest_sub, sub_len = find_longest_common_substring(q_clean, b_clean)

    # 判断条件：子串长度 ≥ 题目长度 × 阈值，且子串是题目全文
    if sub_len >= len(q_clean) * threshold_ratio and longest_sub == q_clean:
        return True
    return False

def recon_image(image_base64):
    """
    调用 API 识别图像中的字符。

    参数:
    - image_base64 (str): 图片的 Base64 编码字符串。
    - token (str): 用户中心 Token。
    - type_code (str): 识别类型代码，默认值为 '10110'。

    返回:
    - 识别结果 (str): 返回识别的文字结果或错误消息。
    """
    api_url = 'https://api.jfbym.com/api/YmServer/customApi'
    token = ""
    type_code = '10110'
    payload = {
        'image': image_base64,
        'token': token,
        'type': type_code
    }
    response = session.post(api_url, json=payload)

    result = response.json()
    if result['code'] == 10000:
        return result['data']['data']
    else:
        return f"请求失败: {result['msg']} (Code: {result['code']})"

def get_captcha():
    times = int(time.time() * 1000)

    params = {
        'time': times,
    }

    response = session.get(
        'https://weiban.mycourse.cn/pharos/login/randLetterImage.do',
        params=params,
        headers=headers,
    )
    with  open("captcha.png", "wb") as f:
        f.write(response.content)
    return recon_image(base64.b64encode(response.content).decode('utf-8')),times

def checkVerifyCode(school_id, userid,userExamPlanId):
    verifyCode,times = get_captcha()
    logger.info(f'验证码: {verifyCode}')

    params = {
        'timestamp': str(int(time.time())),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'time': times,
        'userExamPlanId': userExamPlanId,
        'verifyCode': verifyCode,
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/exam/checkVerifyCode.do',
        params=params,
        data=data,
    )

    return response.json()

def startPaper(school_id, userid, userExamPlanId):
    """
    启动考试试卷函数。

    本函数通过POST请求向指定的URL发送用户考试信息，以启动考试试卷。
    参数:
    - school_id (str): 学校代码。
    - userid (str): 用户ID。
    - userExamPlanId (str): 用户考试计划ID。

    返回:
    - dict: 服务器返回的JSON数据，包含考试试卷相关信息。
    """
    # 初始化参数字典，包含时间戳


    params = {
        'timestamp': str(time.time()),
    }

    # 初始化数据字典，包含tenantCode、userId和userExamPlanId
    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userExamPlanId': userExamPlanId,
    }

    # 发送POST请求到指定URL，携带参数和数据
    response = session.post(
        'https://weiban.mycourse.cn/pharos/exam/startPaper.do',
        params=params,
        data=data,
    )
    # 返回服务器响应的JSON数据
    return response.json()

def listPlan(school_id, userid, userProjectId):
    params = {
        'timestamp': str(time.time()),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userProjectId': userProjectId,
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/exam/listPlan.do',
        params=params,
        headers=headers,
        data=data,
    )

    # print(response.json()["data"][0]["examPlanId"])
    return response.json()
    # ["data"][0]["examPlanId"]

def listHistory(school_id, userid,examPlanId):
    params = {
        'timestamp': str(int(time.time())),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'examPlanId': examPlanId,
        'examType': '2',
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/exam/listHistory.do',
        params=params,
        headers=headers,
        data=data,
    )
    # ["data"][0]["id"]
    return response.json()

def reviewPaper(school_id, userid, userExamIds):
    """
    批量获取多个试卷的题目数据
    :param school_id: 学校ID（tenantCode）
    :param userid: 用户ID
    :param userExamIds: 用户考试ID列表（支持单个或多个ID）
    :return: 拼接后的所有题目数据列表
    """
    all_questions = []
    for userExamId in userExamIds:
        params = {
            'timestamp': str(time.time())
        }
        data = {
            'tenantCode': school_id,
            'userId': userid,
            'userExamId': userExamId,
            'isRetake': '2'
        }


        response = session.post(
            'https://weiban.mycourse.cn/pharos/exam/reviewPaper.do',
            params=params,
            headers=headers,
            data=data,
            timeout=10
        )
        current_questions = response.json().get("data", {}).get("questions", [])
        all_questions.extend(current_questions)

    return all_questions

def getPaper(school_id, userid, userExamIdData):
    userExamIds = []
    for userExamId in userExamIdData['data']:
        userExamIds.append(userExamId["id"])

    # 获取新题目数据
    questions = reviewPaper(school_id, userid, userExamIds)
    question_bank = {}

    # 读取已有的题库文件内容
    try:
        with open('v3.json', 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = {}

    # 原题库中已有题目的数量
    original_count = len(existing_data)

    # 新增题目并加入到题库
    for question in questions:
        question_text = question['title']
        answers = [option['content'] for option in question['optionList'] if option['isCorrect'] == 1]
        question_bank[question_text] = {
            'question': question_text,
            'answers': answers,
            'type': question['type'],
            'typeLabel': question['typeLabel']
        }

    # 合并原题库与新增的题目
    existing_data.update(question_bank)

    # 新增题目的数量
    new_count = len(question_bank)

    # 打印原题库的题目数量和新增的题目数量
    print(f"原题库中的题目数量: {original_count}")
    print(f"新增的题目数量: {new_count}")
    # with open('v3.json', 'w', encoding='utf-8') as file:
    #     json.dump(existing_data, file, ensure_ascii=False, indent=4)

    with open(f'bank_{time.time()}.json', 'w', encoding='utf-8') as simplified_file:
        json.dump(question_bank, simplified_file, ensure_ascii=False, indent=4)

    return existing_data

def submitPaper(school_id, userid,userExamPlanId):
    params = {
        'timestamp': str(int(time.time())),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userExamPlanId': userExamPlanId,
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/exam/submitPaper.do',
        params=params,
        headers=headers,
        data=data
    )
    '''
    {
      "code": "0",
      "data": {
        "score": 98,
        "redpacketInfo": {
          "redpacketName": "",
          "redpacketComment": "",
          "redpacketMoney": 0,
          "isSendRedpacket": 2
        },
        "ebookInfo": {
          "displayBook": 2
        }
      },
      "detailCode": "0"
    }
    '''

    # ["data"]["score"]
    return response.json()

def recordByAi(key,context, maxRetries=3):
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

    for retry in range(maxRetries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "本题为单选题或多选题，请根据题目和选项回答问题，"
                                                  "以json格式输出正确的选项对应的id（即正确选项'id'键对应的值），"
                                                  "单选题示例回答：{\"id\":\"0196739f-f8b7-4d5e-b8c7-6a31eaf631eb\"}，"
                                                  "多选题示例回答,用“,”分隔：{\"id\":\"0196739f-f8b7-4d5e-b8c7-6a31eaf631eb,9994fbfd-bf0b-4b75-bdab-3f0e5cc899bc\"}，"
                                                  "除此之外不要输出任何多余的内容,纯文本,不准markdown。"},
                    {"role": "user", "content": context},
                ],
                stream=False
            )


            json_data = json.loads(response.choices[0].message.content)

            return json_data


        except (RequestException, json.JSONDecodeError, IndexError, KeyError) as e:

            error_type = type(e).__name__
            print(f"第{retry + 1}次请求失败（{error_type}）：{str(e)}")

            # 最后一次重试时抛出异常
            if retry == maxRetries - 1:
                raise

            time.sleep(0.3)

    return None

def findAnswer(key,questions, question_bank):
    found_answers = []
    unfound_questions = []
    bank_titles = list(question_bank.keys())  # 题库题目列表

    for question in questions["data"]["questionList"]:
        question_text = question['title']
        question_id = question['id']
        matched = False

        for bank_title in bank_titles:
            if is_substring_matched(question_text, bank_title):
                # 匹配成功，处理答案
                bank_question = question_bank[bank_title]
                bank_answers = bank_question['answers']
                selected_option_ids = []
                for option in question['optionList']:
                    opt_clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', option['content'])
                    for ans in bank_answers:
                        ans_clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', ans)
                        if opt_clean == ans_clean:
                            selected_option_ids.append(option['id'])
                            break
                if selected_option_ids:
                    found_answers.append({
                        'questionId': question_id,
                        'title': question_text,
                        'answerIds': ','.join(selected_option_ids)
                    })
                    matched = True
                    break # 找到一个匹配项后停止搜索

        if not matched:
            logger.info(f"未找到答案,开启AI答题：{question_text}")
            ansBy = recordByAi(str(key,question))
            logger.info(f'AI回答：{ansBy}')
            if ansBy:
                found_answers.append({
                    'questionId': question_id,
                    'title': question_text,
                    'answerIds': ansBy['id']
                })
            else:
                unfound_questions.append({
                    'questionId': question_id,
                    'title': question_text
                })

    # 输出结果
    print(f"✅ 找到 {len(found_answers)} 题答案，未找到 {len(unfound_questions)} 题")
    print(f"未找到的题目：{unfound_questions}")
    return found_answers

def recordQuestion(questions, school_id,userid,userExamPlanId, examPlanId):
    success_count = 0
    fail_count = 0

    for idx, question in enumerate(questions, 1):

        if not all(key in question for key in ['questionId', 'answerIds']):
            print(f"❌ 第{idx}题参数缺失，开启AI答题")


            fail_count += 1
            continue

        # 生成时间戳（当前时间戳，精确到毫秒可加随机小数）
        timestamp = str(time.time() + random.random() * 0.9)  # 避免连续请求时间戳重复

        # 生成随机用时（在指定范围内）
        useTime = random.randint(200, 600)

        # 构造请求参数
        params = {
            'timestamp': timestamp
        }

        data = {
            'tenantCode': school_id,
            'userId': userid,
            'userExamPlanId': userExamPlanId,
            'questionId': question['questionId'],
            'useTime': useTime,
            'answerIds': question['answerIds'],
            'examPlanId': examPlanId
        }


        response = session.post(
            url='https://weiban.mycourse.cn/pharos/exam/recordQuestion.do',
            params=params,
            data=data,
        )


        time.sleep(useTime / 1000 + random.uniform(1, 5))

        time.sleep(6)
        return response.json()

def preparePaper(school_id, userid, userExamPlanId):
    params = {
        'timestamp': str(time.time()),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userExamPlanId': userExamPlanId,
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/exam/beforePaper.do',
        params=params,
        data=data,
    )
    logger.info(f"获取考试beforePaper: {response.json()}")
    params2 = {
        'timestamp': str(time.time()),
    }

    data2 = {
        'tenantCode': school_id,
        'userId': userid,
        'userExamPlanId': userExamPlanId,
    }

    response2 = session.post(
        'https://weiban.mycourse.cn/pharos/exam/preparePaper.do',
        params=params2,
        headers=headers,
        data=data2,
    )
    logger.info(f"获取考试preparePaper: {response2.json()}")

if __name__ == '__main__':
    key = "" #  deepseek api key
    session.headers["x-token"] = ""
    session.headers["token"] = ""

    school_id = ''

    userid = ''
    userProjectId = ''

    listPlan = listPlan(school_id, userid, userProjectId)
    logger.info(f"获取考试listPlan: {listPlan}")

    examPlanId = listPlan['data'][0]['examPlanId']
    userExamPlanId = listPlan['data'][0]['id']


    listHistory = listHistory(school_id, userid, examPlanId)
    logger.info(f"获取考试listHistory: {listHistory}")

    question_bank = getPaper(school_id, userid, listHistory)
    logger.info(f"获取考试question_bank 题库: success")

    time.sleep(1)
    preparePaper(school_id, userid, userExamPlanId)


    checkVerifyCode = checkVerifyCode(school_id, userid, userExamPlanId)
    logger.info(f"获取考试checkVerifyCode: {checkVerifyCode}")

    questions = startPaper(school_id, userid, userExamPlanId)
    logger.info(f"获取考试questions: {questions}")


    answers = findAnswer(key,questions, question_bank)
    logger.info(f"获取考试answers: {answers}")

    logger.info(f"开始答题recordQuestion: success")

    recordQuestion = recordQuestion(answers, school_id,userid,
                   userExamPlanId,
                   examPlanId)
    logger.info(f"提交答案recordQuestion:{recordQuestion}")
    time.sleep(2.5)


    submitPaper = submitPaper(school_id, userid, userExamPlanId)
    # 分数 ["data"]["score"]
    logger.info(f"提交试卷submitPaper: {submitPaper}")







