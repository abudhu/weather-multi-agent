"""
Setup script for Knowledge IQ (Foundry IQ).

Creates:
  1. A blob knowledge source on Azure AI Search
  2. A knowledge base referencing the knowledge source
  3. A Foundry project connection for MCP access
"""

import json
import sys

import httpx
from azure.identity import AzureCliCredential, get_bearer_token_provider

# ── Configuration ────────────────────────────────────────────────────────────

SUBSCRIPTION_ID = "e957c95d-31a8-4edd-80e9-0da8fa15e65a"
RESOURCE_GROUP = "rg-ambudhu-weather-api-dev"
STORAGE_ACCOUNT = "ambudhuweatherapidev"
CONTAINER_NAME = "weather-data"
FOUNDRY_NAME = "foundry-ambudhu-weather-api-dev"
PROJECT_NAME = "weather-agent-project"
SEARCH_ENDPOINT = "https://search-ambudhu-weather-api-dev.search.windows.net"

KNOWLEDGE_SOURCE_NAME = "weather-blob-ks"
KNOWLEDGE_BASE_NAME = "weather-kb"
CONNECTION_NAME = "weather-kb-mcp"

SEARCH_API_VERSION = "2025-11-01-preview"


# ── Auth helpers ─────────────────────────────────────────────────────────────

credential = AzureCliCredential()

_search_token_provider = get_bearer_token_provider(
    credential, "https://search.azure.com/.default"
)
_arm_token_provider = get_bearer_token_provider(
    credential, "https://management.azure.com/.default"
)


def search_headers() -> dict:
    return {
        "Authorization": f"Bearer {_search_token_provider()}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def arm_headers() -> dict:
    return {
        "Authorization": f"Bearer {_arm_token_provider()}",
        "Content-Type": "application/json",
    }


# ── Step 1: Knowledge Source ─────────────────────────────────────────────────

def create_knowledge_source():
    """Create a blob knowledge source on Azure AI Search."""
    url = (
        f"{SEARCH_ENDPOINT}/knowledgesources('{KNOWLEDGE_SOURCE_NAME}')"
        f"?api-version={SEARCH_API_VERSION}"
    )

    connection_string = (
        f"ResourceId=/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.Storage/storageAccounts/{STORAGE_ACCOUNT};"
    )

    body = {
        "name": KNOWLEDGE_SOURCE_NAME,
        "kind": "azureBlob",
        "description": "7-day weather forecast data for Seattle, Chicago, and Los Angeles.",
        "azureBlobParameters": {
            "connectionString": connection_string,
            "containerName": CONTAINER_NAME,
            "isADLSGen2": False,
        },
    }

    resp = httpx.put(url, json=body, headers=search_headers(), timeout=120)
    if not resp.is_success:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    print(f"  Knowledge source '{KNOWLEDGE_SOURCE_NAME}' created/updated.")
    return resp.json()


# ── Step 2: Knowledge Base ───────────────────────────────────────────────────

def create_knowledge_base():
    """Create a knowledge base referencing the knowledge source."""
    url = (
        f"{SEARCH_ENDPOINT}/knowledgebases('{KNOWLEDGE_BASE_NAME}')"
        f"?api-version={SEARCH_API_VERSION}"
    )

    body = {
        "name": KNOWLEDGE_BASE_NAME,
        "description": "Cached weather forecast data for major US cities.",
        "knowledgeSources": [
            {"name": KNOWLEDGE_SOURCE_NAME},
        ],
        "retrievalReasoningEffort": {"kind": "minimal"},
        "outputMode": "extractiveData",
    }

    resp = httpx.put(url, json=body, headers=search_headers(), timeout=120)
    if not resp.is_success:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    print(f"  Knowledge base '{KNOWLEDGE_BASE_NAME}' created/updated.")
    return resp.json()


# ── Step 3: Foundry Project Connection ───────────────────────────────────────

def create_project_connection():
    """Create a RemoteTool connection on the Foundry project for MCP access."""
    mcp_endpoint = (
        f"{SEARCH_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE_NAME}"
        f"/mcp?api-version={SEARCH_API_VERSION}"
    )

    # CognitiveServices project path (matches our Terraform-created project)
    project_resource_id = (
        f"/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.CognitiveServices"
        f"/accounts/{FOUNDRY_NAME}"
        f"/projects/{PROJECT_NAME}"
    )

    url = (
        f"https://management.azure.com{project_resource_id}"
        f"/connections/{CONNECTION_NAME}?api-version=2025-06-01"
    )

    body = {
        "name": CONNECTION_NAME,
        "type": "Microsoft.CognitiveServices/accounts/projects/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": mcp_endpoint,
            "isSharedToAll": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"},
        },
    }

    resp = httpx.put(url, json=body, headers=arm_headers(), timeout=120)
    if not resp.is_success:
        print(f"  FAILED ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    print(f"  Project connection '{CONNECTION_NAME}' created/updated.")
    return resp.json()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Setting up Knowledge IQ...\n")

    print("Step 1: Creating blob knowledge source...")
    ks = create_knowledge_source()
    print(f"  Done.\n")

    print("Step 2: Creating knowledge base...")
    kb = create_knowledge_base()
    print(f"  Done.\n")

    print("Step 3: Creating Foundry project connection...")
    conn = create_project_connection()
    print(f"  Done.\n")

    mcp_url = (
        f"{SEARCH_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE_NAME}"
        f"/mcp?api-version={SEARCH_API_VERSION}"
    )
    print("Done! Knowledge IQ setup complete.")
    print(f"\nMCP endpoint:\n  {mcp_url}")
    print(f"\nProject connection name:\n  {CONNECTION_NAME}")


if __name__ == "__main__":
    main()
