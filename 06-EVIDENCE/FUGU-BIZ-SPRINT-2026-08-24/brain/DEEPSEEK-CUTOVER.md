# DeepSeek cutover (after Max ends / when owner switches)
1. Put DEEPSEEK_API_KEY in vault secrets (not chat)
2. Set BRAIN_PROVIDER=deepseek on Board2 (+ optional DEEPSEEK_BASE_URL)
3. Keep pipelines unchanged — only BrainPort model map flips
4. Smoke ask(business=ziman) once; compare quality vs fugu samples in evidence
5. Soft budget: DeepSeek pay-as-you-go — set daily USD cap in env before volume
6. Leave SAKANA key vaulted but unused unless owner renews Max
