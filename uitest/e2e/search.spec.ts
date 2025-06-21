import { expect } from "@playwright/test";
import { test } from "./fixture";

test.beforeEach(async ({ page }) => {
  // page.setViewportSize({ width: 400, height: 905 });
  await page.goto("https://www.ebay.com");
  await page.waitForLoadState("networkidle");
});

test("在ebay上搜索商品", async ({
  ai,
  aiQuery,
  aiAssert,
  aiInput,
  aiTap,
  aiScroll, aiWaitFor
}) => {
  // 使用 aiInput 输入搜索关键词
  await aiInput('笔记本电脑', '搜索框');

  // 使用 aiTap 点击搜索按钮
  await aiTap('搜索按钮');

  // 等待搜索结果加载
  await aiWaitFor('搜索结果列表已加载', { timeoutMs: 50000 });

 // 使用 aiScroll 滚动到页面底部
  await aiScroll(
    {
      direction: 'down',
      scrollType: 'once'
    },
    '搜索结果列表'
  );

  // 使用 aiQuery 获取商品信息
  const items = await aiQuery<Array<{title: string, price: number}>>(
    '获取搜索结果中的商品标题和价格'
  );

  console.log("商品信息：", items);
  expect(items?.length).toBeGreaterThan(0);

  // 使用 aiAssert 验证筛选功能
  await aiAssert("界面左侧有类目筛选功能");
});
