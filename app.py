import streamlit as st
import pdfplumber
from docx import Document
import io
from openai import OpenAI
import plotly.graph_objects as go

# ================================
# DeepSeek 接口（新式 OpenAI v1）
# ================================
client = OpenAI(
#api_key="sk-bd5cdc2b6f264620ad88d0f9b084e4c4",
    api_key=st.secrets["OPENAI_API_KEY"],  # 建议在 Streamlit Secrets 里放 API Key
    base_url="https://api.deepseek.com"    # DeepSeek 网关
)

# ================================
# 页面配置
# ================================
st.set_page_config(
    page_title="📄 多维度简历分析 & DeepSeek 专家报告",
    layout="centered"
)

st.title("📄 HR 多维度简历分析 + DeepSeek 智能报告")

# ================================
# 文件上传 + JD 输入
# ================================
uploaded_file = st.file_uploader("📎 上传 PDF/Word 简历", type=["pdf", "docx"])
job_desc = st.text_area("✏️ 输入 JD（岗位描述）")

# ================================
# 解析简历内容
# ================================
def extract_text(file, ext):
    if ext == "pdf":
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            return "\n".join([p.extract_text() or "" for p in pdf.pages])
    elif ext == "docx":
        doc = Document(io.BytesIO(file.read()))
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return ""

# ================================
# 自定义多维度评分示例
# ================================
def local_multi_score(resume_text):
    score = {}

    # 可以按你实际需要加条件或 NLP 模型
    score["学历匹配"] = 90 if "硕士" in resume_text or "博士" in resume_text else 70
    score["工作年限"] = 85 if "5年" in resume_text or "五年" in resume_text else 60
    score["专业相关性"] = 80 if "人力资源" in resume_text or "管理" in resume_text else 50
    score["技能契合"] = 75 if "Python" in resume_text or "数据分析" in resume_text else 55
    score["沟通表达"] = 80 if "沟通" in resume_text else 60
    score["领导潜质"] = 70 if "项目管理" in resume_text else 50

    # 综合平均
    score["综合评分"] = sum(score.values()) / len(score)
    return score

# ================================
# 画雷达图
# ================================
def plot_radar(scores):
    categories = list(scores.keys())[:-1]  # 不含综合
    values = [scores[k] for k in categories]

    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself'
            )
        ]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False
    )
    return fig

# ================================
# DeepSeek 专业版报告生成
# ================================
def deepseek_summary(resume, jd):
    prompt = f"""
你是一名具备十年以上招聘与人才评估经验的资深 HR 咨询顾问，请基于以下简历内容与岗位 JD，生成专业、详细的人才评估报告，报告需包含以下模块：

【1️⃣ 基本匹配分析】
- 分析学历、专业、工作年限、行业经验、岗位经验，每项给出匹配度和简评。

【2️⃣ 能力素质分析】
- 按 KSA 模型（Knowledge, Skills, Abilities, Other Attributes）逐项分析候选人能力亮点与不足。

【3️⃣ 推荐工资区间】
- 结合市场行情与匹配度，给出合理的年薪/月薪建议，并解释原因。

【4️⃣ 岗位适配建议】
- 如果与当前 JD 完全匹配，说明理由；若存在不足，请指出差距，并推荐可胜任的替代岗位。

【5️⃣ 人才画像】
- 用 5~7 句话总结候选人的特点、性格风格、胜任特质、发展潜力、适合的企业文化环境。

【6️⃣ 结论性意见】
- 给招聘经理一句话结论：是否推荐录用、是否建议面试、后续需验证哪些风险点。

请使用专业且客观的中文输出，分模块展示，简洁明了，避免口水话。

---
【简历内容】
{resume[:2000]}

---
【JD】
{jd}

请开始生成完整报告：
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ================================
# 主执行逻辑
# ================================
if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()
    resume_text = extract_text(uploaded_file, ext)
    st.success(f"✅ 简历已解析，约 {len(resume_text)} 字")

    # 多维度本地打分
    scores = local_multi_score(resume_text)
    st.subheader("📊 多维度评分")
    st.write(scores)

    radar = plot_radar(scores)
    st.plotly_chart(radar, use_container_width=True)

    st.subheader("🎯 综合评分")
    st.metric("总分", f"{scores['综合评分']:.1f}")

    if st.button("🔍 DeepSeek 生成专家级报告"):
        if not job_desc.strip():
            st.warning("⚠️ 请先输入 JD！")
        else:
            with st.spinner("DeepSeek 正在分析并生成..."):
                result = deepseek_summary(resume_text, job_desc)
                st.subheader("🤖 DeepSeek 人才画像 & 专家报告")
                st.info(result)