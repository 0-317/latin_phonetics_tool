# 导入 Flask 框架核心模块
from flask import Flask, render_template, request

# 导入核心算法：文本处理 + 统计分析（来自 project/hexingongneng.py）
from project.hexingongneng import process_latin_text, analyze_statistics

# 初始化 Flask 应用
app = Flask(__name__)

# ====================== 多语言配置 ======================
# 俄、中、英 三语言界面文本字典
# 【关键呼应】这里的 L 会直接传给前端 index.html 中的 {{ L.xxx }} 使用
LANGUAGE_MAP = {
    'ru': {
        'lang': 'ru',
        'title': 'Инструмент для разделения слогов латинского текста',
        'input_label': 'Введите латинский текст:',
        'placeholder': 'Например: Arma virumque cano, Troiae qui primus ab oris...',
        'button_text': 'Разделить слоги и проанализировать',
        'stats_title': 'Статистический анализ',
        'total_words': 'Всего слов',
        'total_syllables': 'Всего слогов',
        'structure_title': 'Структура слогов',
        'length_title': 'Долгота слогов',
        'feet_prop_title': 'Пропорция стоп',
        'details_title': 'Детальный анализ стоп',
        'details_desc': 'В этой таблице показан каждый найденный ритмический шаг.',
        'th_num': '№',
        'th_word': 'Слово',
        'th_syllables': 'Слоги',
        'th_open_closed': 'Открытые / Закрытые',
        'th_long_short': 'Долгие / Краткие',
        'th_foot': 'Стопа',
        'no_data': 'Нет данных для анализа.',
        'open': 'Открытый',
        'closed': 'Закрытый',
        'long': 'Долгий',
        'short': 'Краткий',
        'no_results': 'Введите латинский текст и нажмите кнопку.',
        # 音步名称（俄文）
        'foot_names': {
            'SL': 'Ямб',
            'LS': 'Трохей',
            'LL': 'Спондей',
            'SS': 'Пиррихий',
            'SLL': 'Анапест',
            'LLS': 'Дактиль',
            'LSL': 'Амфибрах',
            'LLL': 'Молосс',
            'SSS': 'Трибрах'
        }
    },
    'zh': {
        'lang': 'zh',
        'title': '拉丁语音节分割分析工具',
        'input_label': '请输入拉丁语文本：',
        'placeholder': '例如：Arma virumque cano, Troiae qui primus ab oris...',
        'button_text': '分割音节并分析',
        'stats_title': '统计分析',
        'total_words': '总单词数',
        'total_syllables': '总音节数',
        'structure_title': '音节结构',
        'length_title': '音节长度',
        'feet_prop_title': '音步占比',
        'details_title': '音步详细分析',
        'details_desc': '本表展示所有识别到的韵律音步。',
        'th_num': '序号',
        'th_word': '单词',
        'th_syllables': '音节',
        'th_open_closed': '开闭音节',
        'th_long_short': '长短音节',
        'th_foot': '音步',
        'no_data': '暂无音步分析数据。',
        'open': '开音节',
        'closed': '闭音节',
        'long': '长音节',
        'short': '短音节',
        'no_results': '请输入文本并提交。',
        # 音步名称（中文）
        'foot_names': {
            'SL': '抑扬格',
            'LS': '扬抑格',
            'LL': '扬扬格',
            'SS': '抑抑格',
            'SLL': '抑抑扬格',
            'LLS': '扬抑抑格',
            'LSL': '扬抑扬格',
            'LLL': '三长格',
            'SSS': '三短格'
        }
    },
    'en': {
        'lang': 'en',
        'title': 'Latin Syllable Analysis Tool',
        'input_label': 'Enter Latin text:',
        'placeholder': 'Example: Arma virumque cano, Troiae qui primus ab oris...',
        'button_text': 'Analyze Syllables',
        'stats_title': 'Statistics',
        'total_words': 'Total words',
        'total_syllables': 'Total syllables',
        'structure_title': 'Syllable Structure',
        'length_title': 'Syllable Length',
        'feet_prop_title': 'Foot Proportion',
        'details_title': 'Detailed Foot Analysis',
        'th_num': '#',
        'th_word': 'Word',
        'th_syllables': 'Syllables',
        'th_open_closed': 'Open / Closed',
        'th_long_short': 'Long / Short',
        'th_foot': 'Foot',
        'no_data': 'No foot data available.',
        'open': 'Open',
        'closed': 'Closed',
        'long': 'Long',
        'short': 'Short',
        'no_results': 'Enter text and submit.',
        # 音步名称（英文）
        'foot_names': {
            'SL': 'Iambus',
            'LS': 'Trochee',
            'LL': 'Spondee',
            'SS': 'Pyrrhic',
            'SLL': 'Anapest',
            'LLS': 'Dactyl',
            'LSL': 'Amphibrach',
            'LLL': 'Molossus',
            'SSS': 'Tribrach'
        }
    }
}

# ====================== 经典文本库 ======================
# 内置5段经典拉丁语，前端一键加载
# 【关键呼应】传给前端 index.html 循环渲染按钮
CLASSICTEXTS = [
    {
        "name_ru": "1. Энеида (Вергилий) — начало",
        "name_zh": "1. 埃涅阿斯纪 维吉尔 — 开篇",
        "name_en": "1. Aeneid (Vergil) — opening",
        "text": "Arma virumque cano, Troiae qui primus ab oris Italiam, fato profugus, Lavinaque venit litora."
    },
    {
        "name_ru": "2. Энеида — «Карфаген должен быть разрушен»",
        "name_zh": "2. 埃涅阿斯纪 — 迦太基必将毁灭",
        "name_en": "2. Aeneid — Carthago delenda est",
        "text": "Delenda est Carthago. Ceterum censeo Carthaginem esse delendam."
    },
    {
        "name_ru": "3. O tempora, o mores! (Цицерон)",
        "name_zh": "3. 哦时代！哦风气！（西塞罗）",
        "name_en": "3. O tempora, o mores! (Cicero)",
        "text": "O tempora, o mores! Quid prius dicam de stupris, quid de caedibus?"
    },
    {
        "name_ru": "4. Гаил Юлий Цезарь — «Галлия вся делится на три части»",
        "name_zh": "4. 高卢战记 凯撒 — 整个高卢分为三部分",
        "name_en": "4. Gallic Wars (Caesar) — opening",
        "text": "Gallia est omnis divisa in partes tres, quarum unam incolunt Belgae."
    },
    {
        "name_ru": "5. «Пришел, увидел, победил» (Цезарь)",
        "name_zh": "5. 我来，我见，我征服（凯撒）",
        "name_en": "5. Veni, vidi, vici (Caesar)",
        "text": "Veni, vidi, vici. Ergo omnia vincit amor."
    }
]

# ====================== 主路由（首页） ======================
@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. 获取语言参数（默认俄语）
    lang = request.args.get('lang', 'ru')
    if lang not in LANGUAGE_MAP:
        lang = 'ru'
    L = LANGUAGE_MAP[lang]  # 当前语言包

    # 2. 初始化结果变量
    latin_result = []    # 音节划分原始结果
    stats_data = None    # 图表+表格统计数据

    # 3. 用户提交文本 → 开始分析
    if request.method == 'POST':
        # 获取用户输入
        input_content = request.form.get('latin_text', '').strip()
        
        # 【调用核心算法】音节划分、开闭、长短、重音
        latin_result = process_latin_text(input_content)
        
        # 【调用统计函数】生成图表数据
        if latin_result:
            stats_data = analyze_statistics(latin_result)

            # ====================== 表格数据拼接 ======================
            # 把开闭、长短、音步名称 转为当前语言
            if stats_data and 'feet_details' in stats_data:
                for item in stats_data['feet_details']:
                    for wd in latin_result:
                        if wd['word'] == item['word']:
                            sp = item['syllable_pair'].split('-')
                            if len(sp) == 2:
                                s1, s2 = sp[0], sp[1]
                                s1t = s2t = s1l = s2l = ''
                                # 匹配音节类型
                                for syl in wd['syllables']:
                                    if syl['syllable_str'] == s1:
                                        s1t = syl['type']
                                        s1l = syl['length']
                                    if syl['syllable_str'] == s2:
                                        s2t = syl['type']
                                        s2l = syl['length']

                                # 类型翻译函数
                                def t(v):
                                    if v == 'открытый': return L['open']
                                    if v == 'закрытый': return L['closed']
                                    return ''
                                def l(v):
                                    if v == 'длинный': return L['long']
                                    if v == 'короткий': return L['short']
                                    return ''

                                # 拼接前端表格显示内容
                                item['oc'] = f"{s1} ({t(s1t)}) + {s2} ({t(s2t)})"
                                item['ls'] = f"{s1} ({l(s1l)}) + {s2} ({l(s2l)})"
                                item['name_local'] = L['foot_names'].get(item['pattern'], 'Неизвестно')
                            break

    # 4. 渲染前端页面，把所有数据传给 index.html
    return render_template(
        'index.html', 
        result=latin_result,    # 单词音节结果
        stats=stats_data,       # 统计图表数据
        lang=lang,              # 当前语言
        L=L,                    # 多语言文本
        classic_texts=CLASSICTEXTS  # 经典文本库
    )

# 启动应用
if __name__ == '__main__':
    app.run(debug=True)
