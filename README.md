# 🕯️ The Altar App  

> _“The lot is cast into the lap, but the whole disposing thereof is of the Lord.”_  
> — **Proverbs 16:33**

---

## **Introduction**

Many believers use devotionals to learn God’s Word and reflect on how it applies to their lives. Devotionals can be helpful, but there are moments when we long for something more personal — a word that speaks directly to the situation we’re in.

The **Altar App** is built around a simple idea:  
You flip to a random chapter in Scripture and **trust** that wherever you land, the Holy Spirit intends to speak to you there. Then, you bring both your **situation** and the **chapter** you’ve flipped to before the Lord.

The app’s **Scripture Assistant** will:

- Help you find **parallels** between your current situation and the chapter you’ve landed on.
- Create a **custom devotional**, anchored in God’s Word.
- Encourage you to listen prayerfully for how the Lord might be guiding you.

This app is not meant to replace time in prayer or Scripture but to invite you to **bring your heart to the altar** and seek God’s leading.

---

## **Features**

- 📖 **Random Chapter Selection** — Trust God’s providence.
- 🙏 **Personal Devotionals** — Devotionals are dynamically generated, anchored in Scripture.
- 🔍 **Parallel Discovery** — Highlights connections between your life and God’s Word.
- 🕯️ **Faith-Centered Guidance** — Encourages discernment rooted in prayer.

---

## **Getting Started**

### **Before cloning the repo, head over to [Ollama's website](https://ollama.com/download) and download Ollama if you do not have it installed. Ollama allows you to run powerful LLMs locally and for free!**

#### **After installation, run the following command to confirm its active**
```bash
ollama --version
```

#### Now, simply:
```bash
# See ollama's model list to try out different models. You can replace this model with a different one in altar.py -- just make sure you use this command to pull the model you want to use
ollama pull gpt-oss:20b
```



### **Clone the Repository**

```bash
git clone https://github.com/crc6267/altar-app.git
cd altar-app
```

### **Create and Activate a Virtual Environment**

```bash
python -m venv venv

# Activate the environment:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
### **Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Run the App**

```bash
python chatbot.py
```
