import { test as base } from '@playwright/test';
import type { PlayWrightAiFixtureType } from '@midscene/web/playwright';
import { PlaywrightAiFixture } from '@midscene/web/playwright';
import 'dotenv/config';
export const test = base.extend<PlayWrightAiFixtureType>(PlaywrightAiFixture());
