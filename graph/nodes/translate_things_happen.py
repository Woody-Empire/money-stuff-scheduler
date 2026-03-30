import json
import logging
import os

from langchain_openai import ChatOpenAI

from graph.state import State

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """## 角色

你是一位资深财经新闻翻译专家，精通英中翻译，擅长金融、投资、科技领域术语。

## 任务

用户将提供一个 JSON 对象，包含以下两个字段：

- **`things_happen_text`**（字符串）：Things Happen 板块的纯文本内容，包含多条新闻条目，是翻译的源文本。
- **`things_happen_links`**（数组）：每个元素包含 `text`（英文标题）和 `url`（链接），用于为译文条目附加超链接。

请将 `things_happen_text` 中的每条新闻条目翻译为中文，以 Markdown 无序列表输出，并根据 `things_happen_links` 为对应条目附上超链接。

## 匹配规则

将 `things_happen_text` 中的每条条目与 `things_happen_links` 中的 `text` 字段进行模糊匹配（条目包含该 `text` 即视为匹配成功）。匹配成功则在译文末尾附上链接；未匹配到的条目只输出翻译文本。

## 翻译规则

1. 金融术语使用业内通用中文译法。
2. 公司/机构名：中文译名（英文原名），广为人知的保留英文（如 SpaceX、OpenAI）。
3. 人名：中文音译（英文全名）。
4. 产品/基金名称保留英文不翻译。
5. 译文简洁自然，保留原文语气风格，不添加原文没有的修饰。

## 输出格式

```markdown
## 动态（Things Happen）

- 翻译后的中文条目1 [原文英文标题1](url1)
- 翻译后的中文条目2 [原文英文标题2](url2)
- 翻译后的中文条目3（无匹配链接时不附链接）
- ...
```

**要求：**
- 保持条目顺序与 `things_happen_text` 原文一致。
- 超链接中的 `url` 原样保留，不做任何修改。
- 只输出上述 Markdown 列表，不输出其他内容。"""


async def translate_things_happen(state: State) -> dict:
    if not state.get("things_happen_text"):
        return {"things_happen_translation": ""}

    llm = ChatOpenAI(
        model="anthropic/claude-opus-4.6",
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )

    user_input = json.dumps(
        {
            "things_happen_text": state["things_happen_text"],
            "things_happen_links": state["things_happen_links"],
        },
        ensure_ascii=False,
    )

    response = await llm.ainvoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])

    logger.info("Things Happen 翻译完成，长度: %d", len(response.content))
    return {"things_happen_translation": response.content}
