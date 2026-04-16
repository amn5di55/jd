// monitor.js
// 从环境变量中读取 BARK_TOKEN
const BARK_TOKEN = process.env.BARK_TOKEN;

if (!BARK_TOKEN) {
    console.error("❌ 未设置 BARK_TOKEN 环境变量，程序终止。");
    process.exit(1);
}

const API_URL = "http://jnedu.jinan.gov.cn/api-gateway/jpaas-publish-server/front/page/build/unit?parseType=bulidstatic&webId=9&tplSetId=axTfAe8tlsUy0KvoNeFb5&pageType=column&tagId=%E6%96%B0%E9%97%BB%E5%88%97%E8%A1%A8&editType=null&pageId=18998";
const BARK_URL = `https://api.day.app/${BARK_TOKEN}/`; // 动态拼接 Token
const BASE_DOMAIN = "http://jnedu.jinan.gov.cn";

async function run() {
    try {
        // 1. 请求教育局接口
        const response = await fetch(API_URL, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)',
                'Referer': 'http://jnedu.jinan.gov.cn/col/col18998/index.html'
            },
            // 设置超时时间，避免脚本一直卡住 (需要 Node 18+)
            signal: AbortSignal.timeout(10000) 
        });
        
        if (!response.ok) {
            throw new Error(`请求教育局接口失败，状态码: ${response.status}`);
        }

        const json = await response.json();
        if (!json.success || !json.data) {
            throw new Error("接口返回数据格式异常");
        }

        const html = json.data.html;

        // 2. 利用正则提取链接、标题、日期
        const regex = /<a href="([^"]+)" title="([^"]+)".*?<span>([^<]+)<\/span>/gs;
        let match;
        let msgList = [];

        while ((match = regex.exec(html)) !== null) {
            let [_, href, title, date] = match;
            
            if (!href.startsWith('http')) {
                href = new URL(href, BASE_DOMAIN).href;
            }
            msgList.push(`【${date}】${title}\n${href}`);
        }

        if (msgList.length === 0) {
            throw new Error("未能从HTML中匹配到任何新闻列表");
        }

        const msgBody = msgList.join('\n\n');

        // 3. 将整理好的格式推送到 Bark
        await fetch(BARK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json; charset=utf-8' },
            body: JSON.stringify({
                title: "济南市教育局最新通知",
                body: msgBody,
                group: "教资监控",
                isArchive: 1
            })
        });

        console.log("获取并推送成功");

    } catch (error) {
        console.error("执行出错:", error);
        
        // ================= 新增：失败通知逻辑 =================
        try {
            await fetch(BARK_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json; charset=utf-8' },
                body: JSON.stringify({
                    title: "⚠️ 教资监控运行失败",
                    body: `监控脚本发生异常，请检查服务器或接口。\n错误详情: ${error.message}`,
                    group: "教资监控",
                    level: "timeSensitive" // 让通知更醒目
                })
            });
            console.log("已发送失败通知到手机");
        } catch (pushError) {
            console.error("发送失败通知时网络也断了:", pushError);
        }
    }
}

run();
