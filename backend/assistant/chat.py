import base64
import json
import os

import boto3

from .calculator import calculate_unit_price
from .tools import TOOL_SCHEMA_BEDROCK, format_calculation
from .document_loader import SYSTEM_PROMPT


def _build_bedrock_client():
    absk_key = os.environ.get("LLM_API_KEY", "")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if absk_key.startswith("ABSK"):
        decoded = base64.b64decode(absk_key[4:]).decode()
        access_key, secret_key = decoded.split(":", 1)
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    return boto3.client("bedrock-runtime", region_name=region)


class DocumentAssistant:
    def __init__(self):
        self.client = _build_bedrock_client()
        self.model_id = os.environ.get(
            "LLM_MODEL",
            "arn:aws:bedrock:us-east-1:506715795550:application-inference-profile/dn9mor8k5vrb",
        )

    def ask(self, question: str) -> str:
        messages = [{"role": "user", "content": [{"text": question}]}]

        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOL_SCHEMA_BEDROCK},
            inferenceConfig={"temperature": 0.1, "maxTokens": 800},
        )

        output = response["output"]["message"]
        stop = response["stopReason"]

        if stop == "tool_use":
            messages.append(output)
            tool_results = []
            for block in output["content"]:
                if "toolUse" in block:
                    tool = block["toolUse"]
                    result = calculate_unit_price(**tool["input"])
                    readable = format_calculation(result) if "error" not in result else result["error"]
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool["toolUseId"],
                            "content": [{"text": readable}],
                        }
                    })

            messages.append({"role": "user", "content": tool_results})

            followup = self.client.converse(
                modelId=self.model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=messages,
                toolConfig={"tools": TOOL_SCHEMA_BEDROCK},
                inferenceConfig={"temperature": 0.1, "maxTokens": 800},
            )
            return self._extract_text(followup["output"]["message"])

        return self._extract_text(output)

    @staticmethod
    def _extract_text(message: dict) -> str:
        parts = [b["text"] for b in message.get("content", []) if "text" in b]
        return "\n".join(parts) if parts else "No response generated."
