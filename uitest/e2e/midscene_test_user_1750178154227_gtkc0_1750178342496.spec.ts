import { expect } from "@playwright/test";
import { test } from "./fixture";

test.describe("百度搜索服务验证", () => {
    test.beforeEach(async ({ page }) => {
        // 设置浏览器窗口大小
        page.setViewportSize({ width: 1200, height: 800 });
    });

    test("主流程 - 直接URL访问", async ({ aiQuery, aiInput, aiTap, aiWaitFor, page }) => {
        // 直接使用 Playwright 打开百度页面
        await page.goto("https://www.baidu.com/");

        // 等待百度首页加载完成
        await aiWaitFor("百度首页已加载", {
            selector: "Baidu logo和搜索框",
            timeoutMs: 10000,
        });

        // 在搜索框输入关键词
        await aiInput("今日热点新闻", "百度搜索框");

        // 点击搜索按钮
        await aiTap("百度一下按钮");

        // 等待搜索结果加载
        await aiWaitFor("搜索结果页面已加载", {
            selector: "搜索结果容器",
            timeoutMs: 8000,
        });

        // 验证搜索结果
        const results = await aiQuery<Array<{ title: string }>>(
            "获取搜索结果列表"
        );
        expect(results?.length).toBeGreaterThan(0);
    });

    // test("备选流程 - 书签访问", async ({ aiQuery, aiInput, aiTap, aiWaitFor, page }) => {
    //     // 此流程暂时没有合适的通过书签访问的 Playwright 替代方案，可考虑注释掉或移除该测试用例
    //     // 若要保留，可先模拟直接访问
    //     await page.goto("https://www.baidu.com/");
    //
    //     // 等待百度首页加载完成
    //     await aiWaitFor("百度首页已加载", {
    //         selector: "Baidu logo和搜索框",
    //         timeoutMs: 10000,
    //     });
    //
    //     // 后续步骤与主流程相同
    //     await aiInput("今日热点新闻", "百度搜索框");
    //     await aiTap("百度一下按钮");
    //     await aiWaitFor("搜索结果页面已加载", {
    //         selector: "搜索结果容器",
    //         timeoutMs: 8000,
    //     });
    //     const results = await aiQuery<Array<{ title: string }>>(
    //         "获取搜索结果列表"
    //     );
    //     expect(results?.length).toBeGreaterThan(0);
    // });
    //
    // test("异常处理 - 网络故障", async ({ aiAssert, aiTap, aiWaitFor, page }) => {
    //     // 模拟网络故障
    //     await page.route("**/*", (route) => route.abort());
    //
    //     try {
    //         await page.goto("https://www.baidu.com/");
    //     } catch {}
    //
    //     // 检测页面加载失败
    //     await aiWaitFor("页面加载失败", {
    //         selector: "浏览器错误消息",
    //         timeoutMs: 12000,
    //     });
    //
    //     // 恢复网络
    //     await page.unroute("**/*");
    //
    //     // 直接使用 Playwright 刷新页面，避免通过识别刷新按钮操作
    //     await page.reload();
    //
    //     // 重新检查百度首页加载
    //     await aiWaitFor("百度首页已恢复", {
    //         selector: "Baidu logo和搜索框",
    //         timeoutMs: 15000,
    //     });
    //
    //     // 验证页面恢复
    //     await aiAssert("百度首页元素可见");
    // });
});
