# Running costs (estimates, 2026-10-17)

Prices are from OpenRouter's public model list (https://openrouter.ai/api/v1/models), checked 2026-10-17, in dollars per million tokens.

| Role | Model | Input | Output | Calls per question |
|---|---|---|---|---|
| Forecast | openai/gpt-5.6-luna | 0.20 | 1.20 | 2 |
| Forecast | deepseek/deepseek-v4-pro | 0.21 | 0.42 | 2 |
| Forecast | anthropic/claude-sonnet-5.5 | 2.00 | 10.00 | 1 |
| Research | perplexity/sonar (+ $0.005 per search) | 1.00 | 1.00 | 1 |
| Parsing | openai/gpt-5-nano | 0.05 | 0.40 | about 5 |

## Estimate per question (ESTIMATE)
Assumed sizes: about 5,000 tokens in and 2,000 tokens out per forecast call, and 3,000 in and 1,500 out for research.

| Part | Cost |
|---|---|
| Luna (2 calls) | about $0.007 |
| DeepSeek (2 calls) | about $0.004 |
| Sonnet (1 call) | about $0.030 |
| Research | about $0.010 |
| Parsing | under $0.002 |
| **Total** | **about $0.05–0.06 per question** |

Reasoning models can use more hidden tokens, so plan on up to $0.10.

## The rest of the Fall season
About 550 questions remain: around 250 in the main tournament plus about 60 MiniBench questions every two weeks. That comes to roughly $30–55 for everything.

The prepaid balance is $25 (loaded by the owner 2026-10-17), roughly 250–500 questions.

**The spending limit is OpenRouter's prepaid balance with auto top-up off.** The bot cannot spend more than is loaded. When the balance runs out, forecasts fail and those questions score 0, which costs us nothing extra.
