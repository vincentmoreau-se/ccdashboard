import { expect, test } from "@playwright/test";

const SHOTS = "../docs/superpowers/e2e-screenshots";

test("overview loads and shows KPIs", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "CCDashboard" })).toBeVisible();
  // KPI labels from Overview.tsx
  await expect(page.getByText("Sessions").first()).toBeVisible();
  await expect(page.getByText("Coût total")).toBeVisible();
  // Assert the "Activité & coût par jour" chart genuinely renders bars
  // against real data, and let the Recharts enter-animation settle so the
  // screenshot shows populated bars (not a mid-animation empty chart).
  const bars = page.locator(".recharts-bar-rectangle");
  await bars.first().waitFor({ state: "visible", timeout: 10_000 });
  await expect.poll(async () => bars.count()).toBeGreaterThan(0);
  await page.waitForTimeout(1800); // let Recharts enter-animation settle
  await page.screenshot({ path: `${SHOTS}/overview.png`, fullPage: true });
});

test("navigate Projects -> ProjectDetail -> Session", async ({ page }) => {
  await page.goto("/projects");
  await expect(page.getByRole("heading", { name: "Projets" })).toBeVisible();
  const firstProjectLink = page.locator("table a").first();
  await expect(firstProjectLink).toBeVisible();
  await firstProjectLink.click();
  // ProjectDetail: sessions table; click first session if any
  await expect(page.getByRole("heading", { name: "Sessions" })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/project-detail.png`, fullPage: true });
  const firstSession = page.locator("table a").first();
  if (await firstSession.count()) {
    await firstSession.click();
    await expect(page.getByRole("heading", { name: "Timeline" })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/session.png`, fullPage: true });
  }
});

test("live page renders", async ({ page }) => {
  await page.goto("/live");
  await expect(page.getByRole("heading", { name: /Sessions actives/ })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/live.png`, fullPage: true });
});
