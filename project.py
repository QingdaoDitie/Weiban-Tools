import base64
import json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import logging
import requests
import time
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志记录的最低级别

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建文件处理器，用于写入日志文件
file_handler = logging.FileHandler('weiban_study.log', encoding='utf-8')
file_handler.setFormatter(formatter)

# 创建控制台处理器，用于输出到控制台
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 将处理器添加到记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

session = requests.Session()
base_url = "https://weiban.mycourse.cn/"

headers = {
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'priority': 'i',
        'referer': 'https://weiban.mycourse.cn/',
        'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
}
key = ""

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
    token = key
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

def encrypt(data) -> str:
    """
    AES加密
    :param data: json 字符串
    :return: base64 编码的加密字符串
    """
    key = urlsafe_b64decode("d2JzNTEyAAAAAAAAAAAAAA==")  # wbs512
    return urlsafe_b64encode(AES.new(key, AES.MODE_ECB).encrypt(pad(data.encode(), AES.block_size))).decode()

def login(username, password,school_id):
    url = f"{base_url}/pharos/login/login.do"
    params = {"timestamp": str(time.time())}

    logger.info(f"开始登录:{username}")

    captcha_code, captcha_time = get_captcha()

    logger.info(f"✅获取验证码成功:{captcha_code}")
    data = {
        "keyNumber": username,
        "password": password,
        "tenantCode": school_id,
        "time": captcha_time,
        "verifyCode": captcha_code,
    }

    json_data = json.dumps(data, separators=(",", ":"))

    # 对 JSON 字符串进行 Base64 编码
    encoded_data = encrypt(json_data)

    response = session.post(url, params=params, data={"data": encoded_data})
    if response.json().get("data", {}).get("token"):
        user = response.json().get("data")
        session.headers["X-Token"] = user.get("token")
        logger.info(f"✅登录成功: Name:{user.get('realName')} | token:{user.get('token')} | userId:{user.get('userId')}")
    return response.json()

def get_all_course_list(school_id,user_id):

    params = {
        'timestamp':str(time.time()),
    }

    data = {
        'tenantCode':school_id,
        'userId': user_id
    }
    # print(data, school_id, user_id,  params)
    response = session.post(
        'https://weiban.mycourse.cn/pharos/index/listStudyTask.do',
        params=params,
        headers=headers,
        data=data,
    )
    return response.json()

# 获取课程详情: {project_id}
def get_course_detail(userProjectId,  school_id, userid):
    params = {
        'timestamp': str(time.time()),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userProjectId': userProjectId,
        'chooseType': '3',
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/usercourse/listCategory.do',
        params=params,
        headers=headers,
        data=data,
    )
    # print(data)
    # print(response.text)
    return response.json()

def get_course_list(categoryCode, userProjectId, userid, school_id):
    params = {
        'timestamp': str(time.time()),
    }
    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userProjectId': userProjectId,
        'chooseType': '3',
        'categoryCode': categoryCode,
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/usercourse/listCourse.do',
        params=params,
        headers=headers,
        data=data,
    )
    return response.json()

def Simulate_learn(resourceId, userProjectId,userCourseId,  userid, school_id):
    params = {
        'timestamp': str(time.time()),
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'courseId': resourceId,
        'userProjectId': userProjectId,
    }

    response = session.post(
        'https://weiban.mycourse.cn/pharos/usercourse/study.do',
        params=params,
        headers=headers,
        data=data,
    )
    logger.info(f"开始模拟学习study:{response.text}")
    time.sleep(random.uniform(0.5, 1))

    params12 = {
        'timestamp': str(time.time()),
    }

    data12 = {
        'tenantCode': school_id,
        'userId': userid,
    }

    response = requests.post(
        'https://weiban.mycourse.cn/pharos/tenantconfig/getSimpleConfig.do',
        params=params12,
        headers=headers,
        data=data12,
    )
    logger.info(f"获取学习资料v2-getSimpleConfig:{response.text}")
    time.sleep(random.uniform(0.5, 1))

    params = {
        'timestamp': str(time.time()),
    }
    response = session.post(
        'https://weiban.mycourse.cn/pharos/usercourse/getCourseUrl.do',
        params=params,
        headers=headers,
        data=data,
    )
    logger.info(f"获取学习资料getCourseUrl:{response.text}")


    time.sleep(random.uniform(20, 24))

    params4 = {
        'userCourseId': userCourseId,
        'userProjectId': userProjectId,
        'userId': userid,
        'tenantCode': school_id


    }
    response = session.get('https://weiban.mycourse.cn/pharos/usercourse/getCaptcha.do',
                            headers=headers,params=params4)

    data4 = response.json()
    logger.info(f"获取验证码getCaptcha:{data4}")
    time.sleep(random.uniform(0.5, 1))
    # print(data4)
    # print(data4["captcha"]["questionId"])
    questionId = data4["captcha"]["questionId"]
    params2 ={
        'userCourseId': userCourseId,
        'userProjectId': userProjectId,
        'userId': userid,
        'tenantCode': school_id,
        'questionId': questionId,

    }

    data2 = {
        'coordinateXYs': '[{"x":66,"y":420},{"x":141,"y":425},{"x":211,"y":426}]',
    }

    coordinates = json.loads(data2['coordinateXYs'])

    for coord in coordinates:
        coord['x'] += random.randint(-2, 2)
        coord['y'] += random.randint(-2, 2)

    data2['coordinateXYs'] = json.dumps(coordinates)
    response2 = session.post('https://weiban.mycourse.cn/pharos/usercourse/checkCaptcha.do', params=params2,
                              headers=headers, data=data2)

    data2 = response2.json()
    logger.info(f"验证码验证checkCaptcha:{data2}")
    time.sleep(random.uniform(0.5, 1))
    #print(data2)
    #print(data2["data"]["methodToken"])
    methodToken = data2["data"]["methodToken"]
    timestamp = int(time.time() * 1000)
    params4 = {
        'callback': f'jQuery34106576461271809699_{timestamp}',
        'userCourseId': userCourseId,
        'tenantCode': school_id,
        '_': f'{str(timestamp + random.randint(1,2))}',

    }

    response4 = session.get(
        f'https://weiban.mycourse.cn/pharos/usercourse/v2/{methodToken}.do',
        params=params4,
        headers=headers,
    )
    logger.info(f"验证码验证v2-methodToken:{response4.text}")
    time.sleep(random.uniform(0.5, 1))

    # print(response4.text)

    data6 = {
        'tenantCode': school_id,
        'userId': userid,
        'currentUserId': userid,
        'targetId': resourceId,
        'service': '/comment/comment/getDetail.api',
        'clientId': 'operation'
    }

    import execjs

    # 加载并执行 demo.js 文件
    with open('demo.js', 'r', encoding='utf-8') as f:
        js_code = f.read()

    # 编译并运行 JavaScript 代码
    context = execjs.compile(js_code)

    # 调用 JavaScript 中的函数 'a' 并获取返回值
    result = context.call('createSign', data6)
    data7 = {
        'tenantCode': school_id,
        'userId': userid,
        'currentUserId': userid,
        'targetId': resourceId,
        'service': '/comment/comment/getDetail.api',
        'clientId': 'operation',
        'sign':result
    }

    # print(result)
    session.headers["Token"] = token
    response6 = session.post('https://safety.mycourse.cn/brainprovider/router', headers=headers, data=data7)
    logger.info(f"模拟获取评论v2-router:{response6.text}")
    time.sleep(random.uniform(0.5, 1))

    # print(response6.text)

    time.sleep(random.uniform(1, 2))
    params = {
        'timestamp': f"{time.time():.2f}",
    }

    data = {
        'tenantCode': school_id,
        'userId': userid,
        'userCourseId': userCourseId,
    }

    response7 = session.post(
        'https://weiban.mycourse.cn/pharos/resource/getNear.do',
        params=params,
        headers=headers,
        data=data,
    )
    logger.info(f"模拟获取学习资料getNear:{response7.text}")


if __name__ == '__main__':
    logger.info("Starting")

    username = ''
    password = ''
    school_id = ""

    login_data = login(username, password, school_id)

    logger.info(f"✅获取登录个人信息成功：{login_data}")

    token = login_data['data']["token"]
    userid = login_data['data']["userId"]
    session.headers["X-Token"] = token
    session.headers["Token"] = token
    listStudyTask = get_all_course_list(school_id,userid)

    logger.info(f"✅获取本学期数据成功:{listStudyTask['data']}")


    projectId = [project.get('projectId') for project in listStudyTask['data'] if
                 project.get('studyStateLabel') == '未完成']
    userProjectIds = [project.get('userProjectId') for project in listStudyTask['data'] if
                     project.get('studyStateLabel') == '未完成']
    projectName = [project.get('projectName') for project in listStudyTask['data'] if
                      project.get('studyStateLabel') == '未完成']
    endTime = [project.get('endTime') for project in listStudyTask['data'] if
                   project.get('studyStateLabel') == '未完成']
    logger.info(f"✅获取未完成课程详情成功:{userProjectIds,projectName,endTime}")

    for userProjectId,projectName_item,endTime_item in zip(userProjectIds,projectName,endTime):
        logger.info(f"正在学习课程：userProjectId:{userProjectId},projectName:{projectName_item},endTime:{endTime_item}")

        listCategory = get_course_detail(userProjectId, school_id,userid)


        categoryCodes = [category.get('categoryCode') for category in listCategory['data'] if
                         category.get('totalNum') > category.get('finishedNum')]
        categoryName = [category.get('categoryName') for category in listCategory['data'] if
                         category.get('totalNum') > category.get('finishedNum')]
        Num = [category.get('totalNum')-category.get('finishedNum') for category in listCategory['data'] if
                         category.get('totalNum') > category.get('finishedNum')]

        logger.info(f"✅获取未完成章节信息成功:{categoryCodes,categoryName,Num}")
        for categoryCodes_item,categoryName_item,Num_item in zip(categoryCodes,categoryName,Num):

            logger.info(f"正在学习章节:{categoryCodes_item}-{categoryName_item}-剩余课程：{Num_item}")
            number = 1
            category_ = get_course_list(categoryCodes_item,userProjectId,userid, school_id)
            for category_item in category_.get('data'):
                resourceId = category_item.get('resourceId')
                userCourseId = category_item.get('userCourseId')
                categoryName = category_item.get('categoryName')
                resourceName = category_item.get('resourceName')
                logger.info(f"正在学习课时: {number}/{Num_item} - {categoryName} - {resourceName} - resourceId:{resourceId} - userCourseId:{userCourseId}")


                Simulate_learn(resourceId, userProjectId,userCourseId, userid,school_id)

                logger.info(f"✅完成课时: {number}/{Num_item} - {categoryName} - {resourceName} - resourceId:{resourceId} - userCourseId:{userCourseId}")
                number = number + 1
                time.sleep(random.uniform(3, 5))


            logger.info(f"✅完成章节:{categoryCodes_item}-{categoryName}")
        logger.info(f"✅完成课程:{projectName}-{userProjectId}")
    user = login_data.get("data")
    logger.info(f"✅全部课程学习完成-{user.get('realName')}, token:{user.get('token')}, userId:{user.get('userId')}")
